"""Serveur web local de suivi des impayés (stdlib uniquement).

Lancement : python3 app/server.py [--port 8000] [--db suivi_impayes.db]
Accès : http://127.0.0.1:8000  (boucle locale uniquement)
"""
import argparse
import csv
import io
import json
import os
import re
import sqlite3
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from db import connect, init_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DEFAULT_DB = os.path.join(BASE_DIR, "suivi_impayes.db")

HOST = "127.0.0.1"


def today():
    return date.today()


def anciennete(echeance):
    try:
        d = date.fromisoformat(echeance)
    except (ValueError, TypeError):
        return None
    return (today() - d).days


def tranche(jours):
    if jours is None or jours < 0:
        return "À échoir"
    if jours <= 30:
        return "0-30 j"
    if jours <= 60:
        return "31-60 j"
    if jours <= 90:
        return "61-90 j"
    return "> 90 j"


def prochaine_action(tr):
    return {
        "À échoir": "Surveiller l'échéance",
        "0-30 j": "Email de relance J+7",
        "31-60 j": "Email J+15 + SMS",
        "61-90 j": "Mise en demeure LRAR (J+30)",
        "> 90 j": "Appel J+45 / échelonnement J+60 / injonction",
    }.get(tr, "Relancer")


def row_to_dict(row):
    return dict(row) if row is not None else None


class Api:
    def __init__(self, db_path):
        self.db_path = db_path

    def conn(self):
        return connect(self.db_path)

    def query(self, sql, params=()):
        c = self.conn()
        try:
            return [dict(r) for r in c.execute(sql, params).fetchall()]
        finally:
            c.close()

    def one(self, sql, params=()):
        c = self.conn()
        try:
            r = c.execute(sql, params).fetchone()
            return dict(r) if r else None
        finally:
            c.close()

    def execute(self, sql, params=()):
        c = self.conn()
        try:
            cur = c.execute(sql, params)
            c.commit()
            return cur.lastrowid
        finally:
            c.close()

    def dashboard(self):
        encours = self.one(
            "SELECT COALESCE(SUM(f.montant_ht*(1+f.tva_pct/100) - f.acompte - COALESCE(p.total,0)),0) AS encours, "
            "COUNT(i.id) AS nb FROM impayes i JOIN factures f ON f.id=i.facture_id "
            "LEFT JOIN (SELECT facture_id, SUM(montant) total FROM paiements GROUP BY facture_id) p ON p.facture_id=f.id "
            "WHERE i.statut NOT IN ('Résolu','Irrécouvrable')"
        )
        tranches = self.query(
            "SELECT f.date_echeance, i.id FROM impayes i JOIN factures f ON f.id=i.facture_id "
            "WHERE i.statut NOT IN ('Résolu','Irrécouvrable')"
        )
        counts = {"À échoir": 0, "0-30 j": 0, "31-60 j": 0, "61-90 j": 0, "> 90 j": 0}
        for t in tranches:
            counts[tranche(anciennete(t["date_echeance"]))] += 1
        relances_semaine = self.one(
            "SELECT COUNT(*) AS n FROM relances WHERE date >= ?",
            (today() - timedelta(days=7),),
        )["n"]
        recouvré = self.one(
            "SELECT COALESCE(SUM(montant),0) AS m FROM paiements WHERE strftime('%Y-%m', date) = ?",
            (today().strftime("%Y-%m"),),
        )["m"]
        dso = self.one(
            "SELECT AVG(julianday(p.date) - julianday(f.date_facture)) AS dso FROM paiements p "
            "JOIN factures f ON f.id = p.facture_id"
        )["dso"]
        return {
            "encours_impaye": round(encours["encours"], 2),
            "nb_impayes_ouverts": encours["nb"],
            "repartition_tranches": counts,
            "relances_7_jours": relances_semaine,
            "recouvre_ce_mois": round(recouvré, 2),
            "dso_jours": round(dso, 1) if dso else None,
        }

    def impayes_list(self, filtre=None):
        sql = (
            "SELECT i.id, i.code, i.niveau_relance, i.prochaine_action, i.statut, i.responsable, "
            "f.numero AS facture, f.date_echeance, f.prestation, "
            "f.montant_ht*(1+f.tva_pct/100) - f.acompte - COALESCE(p.total,0) AS reste_du, "
            "c.code AS client_code, c.nom AS client_nom, c.prenom AS client_prenom, c.telephone, c.email, "
            "(SELECT MAX(date) FROM relances r WHERE r.impaye_id = i.id) AS derniere_relance "
            "FROM impayes i JOIN factures f ON f.id = i.facture_id JOIN clients c ON c.id = f.client_id "
            "LEFT JOIN (SELECT facture_id, SUM(montant) total FROM paiements GROUP BY facture_id) p ON p.facture_id = f.id "
            "WHERE i.statut NOT IN ('Résolu','Irrécouvrable')"
        )
        params = ()
        if filtre == "a-relancer":
            sql += " AND f.date_echeance <= ?"
            params = (today().isoformat(),)
        sql += " ORDER BY f.date_echeance ASC"
        rows = self.query(sql, params)
        for r in rows:
            r["anciennete"] = anciennete(r["date_echeance"])
            r["tranche"] = tranche(r["anciennete"])
            if not r["prochaine_action"]:
                r["prochaine_action"] = prochaine_action(r["tranche"])
        return rows

    def clients_list(self):
        return self.query(
            "SELECT c.*, (SELECT COUNT(*) FROM impayes i JOIN factures f ON f.id=i.facture_id "
            "WHERE f.client_id=c.id AND i.statut NOT IN ('Résolu','Irrécouvrable')) AS nb_impayes, "
            "(SELECT COALESCE(SUM(f.montant_ht*(1+f.tva_pct/100)-f.acompte-COALESCE(p.total,0)),0) FROM factures f "
            "LEFT JOIN (SELECT facture_id, SUM(montant) total FROM paiements GROUP BY facture_id) p ON p.facture_id=f.id "
            "JOIN impayes i ON i.facture_id=f.id AND i.statut NOT IN ('Résolu','Irrécouvrable') WHERE f.client_id=c.id) AS total_impaye "
            "FROM clients c ORDER BY c.nom"
        )

    def factures_list(self):
        rows = self.query(
            "SELECT f.*, c.code AS client_code, c.nom AS client_nom, c.prenom AS client_prenom, "
            "a.nom AS animal_nom, COALESCE(p.total,0) AS paye, "
            "f.montant_ht*(1+f.tva_pct/100) - f.acompte - COALESCE(p.total,0) AS reste_du "
            "FROM factures f JOIN clients c ON c.id=f.client_id LEFT JOIN animaux a ON a.id=f.animal_id "
            "LEFT JOIN (SELECT facture_id, SUM(montant) total FROM paiements GROUP BY facture_id) p ON p.facture_id=f.id "
            "ORDER BY f.date_facture DESC"
        )
        for r in rows:
            r["montant_ttc"] = round(r["montant_ht"] * (1 + r["tva_pct"] / 100), 2)
            r["reste_du"] = round(max(0, r["reste_du"]), 2)
            r["anciennete"] = anciennete(r["date_echeance"])
        return rows

    def relances_list(self):
        return self.query(
            "SELECT r.*, i.code AS impaye_code, f.numero AS facture, c.nom AS client_nom, c.prenom AS client_prenom "
            "FROM relances r JOIN impayes i ON i.id=r.impaye_id JOIN factures f ON f.id=i.facture_id "
            "JOIN clients c ON c.id=f.client_id ORDER BY r.date DESC, r.id DESC"
        )

    def paiements_list(self):
        return self.query(
            "SELECT p.*, f.numero AS facture, c.nom AS client_nom, c.prenom AS client_prenom "
            "FROM paiements p JOIN factures f ON f.id=p.facture_id JOIN clients c ON c.id=f.client_id "
            "ORDER BY p.date DESC, p.id DESC"
        )

    def client_detail(self, client_id):
        client = self.one("SELECT * FROM clients WHERE id=?", (client_id,))
        if not client:
            return None
        client["animaux"] = self.query("SELECT * FROM animaux WHERE client_id=?", (client_id,))
        client["factures"] = self.query(
            "SELECT f.*, COALESCE(p.total,0) AS paye, f.montant_ht*(1+f.tva_pct/100)-f.acompte-COALESCE(p.total,0) AS reste_du "
            "FROM factures f LEFT JOIN (SELECT facture_id, SUM(montant) total FROM paiements GROUP BY facture_id) p ON p.facture_id=f.id "
            "WHERE f.client_id=? ORDER BY f.date_facture DESC", (client_id,))
        client["relances"] = self.query(
            "SELECT r.*, i.code AS impaye_code FROM relances r JOIN impayes i ON i.id=r.impaye_id "
            "JOIN factures f ON f.id=i.facture_id WHERE f.client_id=? ORDER BY r.date DESC", (client_id,))
        return client

    def creer_impaye(self, facture_id, niveau="Aucun", action="", responsable=""):
        n = self.one("SELECT COALESCE(MAX(CAST(SUBSTR(code,5) AS INTEGER)),0)+1 AS n FROM impayes")["n"]
        code = f"IMP-{n:03d}"
        return self.execute(
            "INSERT INTO impayes (code, facture_id, niveau_relance, prochaine_action, statut, responsable) VALUES (?,?,?,?, 'Ouvert', ?)",
            (code, facture_id, niveau, action, responsable))

    def maj_statut_facture(self, facture_id):
        f = self.one("SELECT montant_ht, tva_pct, acompte FROM factures WHERE id=?", (facture_id,))
        if not f:
            return
        paye = self.one("SELECT COALESCE(SUM(montant),0) AS t FROM paiements WHERE facture_id=?", (facture_id,))["t"]
        ttc = f["montant_ht"] * (1 + f["tva_pct"] / 100)
        reste = ttc - f["acompte"] - paye
        statut = "Payée" if reste <= 0.005 else ("Partielle" if reste < ttc - 0.005 else "Impayée")
        self.execute("UPDATE factures SET statut=? WHERE id=?", (statut, facture_id))
        if statut == "Impayée":
            existe = self.one("SELECT id FROM impayes WHERE facture_id=?", (facture_id,))
            if not existe:
                self.creer_impaye(facture_id)
        else:
            self.execute("DELETE FROM impayes WHERE facture_id=? AND statut='Ouvert'", (facture_id,))


VALID = {
    "clients": {"nom": str, "prenom": str, "telephone": str, "email": str, "adresse": str,
                "code_postal": str, "ville": str, "canal_prefere": str, "mode_paiement": str, "statut": str},
    "factures": {"numero": str, "date_facture": str, "prestation": str, "categorie": str,
                 "date_echeance": str, "statut": str},
    "paiements": {"date": str, "moyen": str, "reference": str, "notes": str},
    "relances": {"date": str, "canal": str, "effectuee_par": str, "contact": str, "resume": str,
                 "reponse_client": str, "date_promesse": str, "resultat": str},
    "impayes": {"niveau_relance": str, "prochaine_action": str, "statut": str, "responsable": str},
}


def safe_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


class Handler(BaseHTTPRequestHandler):
    api = None
    server_version = "SuiviImpayes/1.0"

    def log_message(self, fmt, *args):
        pass

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, text, status=200):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _csv(self, filename, header, rows):
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(header)
        w.writerows(rows)
        data = buf.getvalue().encode("utf-8-sig")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)
        api = self.api

        if path == "/" or path == "/index.html":
            with open(os.path.join(STATIC_DIR, "index.html"), encoding="utf-8") as f:
                self._html(f.read())
            return
        if path.startswith("/static/"):
            fp = os.path.normpath(os.path.join(STATIC_DIR, path[len("/static/"):]))
            if fp.startswith(STATIC_DIR) and os.path.isfile(fp):
                with open(fp, "rb") as f:
                    data = f.read()
                ctype = "text/css" if fp.endswith(".css") else "application/javascript" if fp.endswith(".js") else "application/octet-stream"
                self.send_response(200)
                self.send_header("Content-Type", ctype + ("; charset=utf-8" if "text" in ctype or "javascript" in ctype else ""))
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            self._json({"error": "not found"}, 404)
            return

        if path == "/api/dashboard":
            self._json(api.dashboard())
        elif path == "/api/impayes":
            self._json(api.impayes_list(qs.get("filtre", [None])[0]))
        elif path == "/api/clients":
            self._json(api.clients_list())
        elif path == "/api/factures":
            self._json(api.factures_list())
        elif path == "/api/relances":
            self._json(api.relances_list())
        elif path == "/api/paiements":
            self._json(api.paiements_list())
        elif path.startswith("/api/clients/"):
            cid = safe_int(path.split("/")[-1])
            detail = api.client_detail(cid) if cid else None
            if detail:
                self._json(detail)
            else:
                self._json({"error": "client introuvable"}, 404)
        elif path == "/api/export/impayes.csv":
            rows = api.impayes_list()
            self._csv("impayes.csv",
                      ["code", "facture", "client", "reste_du", "date_echeance", "anciennete", "tranche",
                       "niveau_relance", "prochaine_action", "statut", "responsable", "derniere_relance"],
                      [[r.get(k) for k in ["code", "facture", "client_code", "reste_du", "date_echeance",
                                          "anciennete", "tranche", "niveau_relance", "prochaine_action",
                                          "statut", "responsable", "derniere_relance"]] for r in rows])
        elif path == "/api/export/relances.csv":
            rows = api.relances_list()
            self._csv("relances.csv",
                      ["date", "impaye", "facture", "client", "canal", "effectuee_par", "contact",
                       "resume", "reponse_client", "date_promesse", "resultat"],
                      [[r.get(k) for k in ["date", "impaye_code", "facture", "client_nom", "canal",
                                          "effectuee_par", "contact", "resume", "reponse_client",
                                          "date_promesse", "resultat"]] for r in rows])
        elif path == "/api/modeles":
            self._json(MODELES)
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        data = self._body()
        api = self.api

        try:
            if path == "/api/clients":
                n = api.one("SELECT COALESCE(MAX(CAST(SUBSTR(code,5) AS INTEGER)),0)+1 AS n FROM clients")["n"]
                code = f"CLI-{n:03d}"
                api.execute(
                    "INSERT INTO clients (code,nom,prenom,telephone,email,adresse,code_postal,ville,consentement_relance,canal_prefere,mode_paiement,statut) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (code, data.get("nom", ""), data.get("prenom", ""), data.get("telephone", ""),
                     data.get("email", ""), data.get("adresse", ""), data.get("code_postal", ""),
                     data.get("ville", ""), 1 if data.get("consentement_relance") else 0,
                     data.get("canal_prefere", "Email"), data.get("mode_paiement", "CB"),
                     data.get("statut", "Actif")))
                self._json({"ok": True, "code": code}, 201)

            elif path == "/api/factures":
                numero = data.get("numero") or f"FAC-{today().strftime('%Y')}-{api.one('SELECT COALESCE(MAX(CAST(SUBSTR(numero,-4) AS INTEGER)),0)+1 AS n FROM factures')['n']:04d}"
                ht = float(data.get("montant_ht") or 0)
                tva = float(data.get("tva_pct") or 10)
                acompte = float(data.get("acompte") or 0)
                echeance = data.get("date_echeance") or (today() + timedelta(days=30)).isoformat()
                fid = api.execute(
                    "INSERT INTO factures (numero,date_facture,client_id,animal_id,prestation,categorie,montant_ht,tva_pct,acompte,date_echeance,statut) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (numero, data.get("date_facture") or today().isoformat(), safe_int(data.get("client_id")),
                     safe_int(data.get("animal_id")), data.get("prestation", ""), data.get("categorie", "Autre"),
                     ht, tva, acompte, echeance, "Impayée"))
                api.maj_statut_facture(fid)
                self._json({"ok": True, "id": fid, "numero": numero}, 201)

            elif path == "/api/paiements":
                fid = safe_int(data.get("facture_id"))
                if not fid:
                    self._json({"error": "facture_id requis"}, 400)
                    return
                pid = api.execute(
                    "INSERT INTO paiements (date,facture_id,montant,moyen,reference,notes) VALUES (?,?,?,?,?,?)",
                    (data.get("date") or today().isoformat(), fid, float(data.get("montant") or 0),
                     data.get("moyen", "CB"), data.get("reference", ""), data.get("notes", "")))
                api.maj_statut_facture(fid)
                self._json({"ok": True, "id": pid}, 201)

            elif path == "/api/relances":
                iid = safe_int(data.get("impaye_id"))
                if not iid:
                    self._json({"error": "impaye_id requis"}, 400)
                    return
                rid = api.execute(
                    "INSERT INTO relances (date,impaye_id,canal,effectuee_par,contact,resume,reponse_client,date_promesse,resultat) VALUES (?,?,?,?,?,?,?,?,?)",
                    (data.get("date") or today().isoformat(), iid, data.get("canal", "Email"),
                     data.get("effectuee_par", ""), data.get("contact", ""), data.get("resume", ""),
                     data.get("reponse_client", "Aucune"), data.get("date_promesse", ""),
                     data.get("resultat", "À relancer")))
                self._json({"ok": True, "id": rid}, 201)

            elif path == "/api/impayes/creer":
                fid = safe_int(data.get("facture_id"))
                existe = api.one("SELECT id FROM impayes WHERE facture_id=?", (fid,)) if fid else None
                if existe:
                    self._json({"ok": True, "id": existe["id"], "deja_existant": True})
                else:
                    iid = api.creer_impaye(fid, data.get("niveau", "Aucun"), data.get("action", ""), data.get("responsable", ""))
                    self._json({"ok": True, "id": iid}, 201)

            else:
                self._json({"error": "not found"}, 404)
        except (ValueError, sqlite3.IntegrityError) as e:
            self._json({"error": str(e)}, 400)

    def do_PATCH(self):
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        data = self._body()
        api = self.api
        if len(parts) == 3 and parts[0] == "api":
            table, idraw = parts[1], parts[2]
            rid = safe_int(idraw)
            if table in VALID and rid:
                cols = [k for k in data.keys() if k in VALID[table]]
                if cols:
                    sql = f"UPDATE {table} SET " + ", ".join(f"{c}=?" for c in cols) + " WHERE id=?"
                    api.execute(sql, [data[c] for c in cols] + [rid])
                    if table == "impayes":
                        fid = api.one("SELECT facture_id FROM impayes WHERE id=?", (rid,))
                        if fid:
                            api.maj_statut_facture(fid["facture_id"])
                    self._json({"ok": True})
                    return
            self._json({"error": "requête invalide"}, 400)
            return
        self._json({"error": "not found"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        api = self.api
        if len(parts) == 3 and parts[0] == "api":
            table, idraw = parts[1], parts[2]
            rid = safe_int(idraw)
            allowed = {"clients", "factures", "paiements", "relances", "impayes", "animaux"}
            if table in allowed and rid:
                if table == "factures":
                    api.execute("DELETE FROM impayes WHERE facture_id=?", (rid,))
                api.execute(f"DELETE FROM {table} WHERE id=?", (rid,))
                self._json({"ok": True})
                return
        self._json({"error": "not found"}, 404)


MODELES = {
    "J+7": {
        "objet": "Facture n° {facture} — échéance dépassée de quelques jours",
        "corps": ("Bonjour {prenom} {nom},\n\nSauf erreur de notre part, nous n'avons pas encore reçu "
                  "le règlement de la facture n° {facture} du {date_facture}, d'un montant de {montant} €, "
                  "concernant {prestation}, échue le {echeance}.\n\nMerci de procéder au paiement dans les "
                  "meilleurs délais. En cas de difficulté, contactez-nous : nous trouverons une solution "
                  "(échelonnement).\n\nBien cordialement,\n{clinique} — {telephone} — {email}")
    },
    "J+15": {
        "objet": "Relance n° 2 — Facture n° {facture} toujours impayée",
        "corps": ("Bonjour {prenom} {nom},\n\nMalgré notre précédent message, la facture n° {facture} "
                  "({montant} €, échue le {echeance}) reste impayée ({jours} jours de retard). Merci de "
                  "régulariser sous 8 jours, à défaut nous engagerons une mise en demeure avec frais et "
                  "pénalités prévus par la loi.\n\n{clinique}")
    },
    "SMS": {
        "objet": "SMS",
        "corps": ("{clinique} : facture n° {facture} de {montant} € impayée depuis le {echeance}. "
                  "Merci de régulariser sous 8 jours ou appelez le {telephone}.")
    },
    "J+30": {
        "objet": "Mise en demeure de payer — Facture n° {facture} (LRAR)",
        "corps": ("Madame, Monsieur {nom},\n\nPar courrier recommandé avec accusé de réception, nous vous "
                  "mettons en demeure de régler la somme de {montant} € (facture n° {facture} du "
                  "{date_facture}, échue le {echeance}, relative à {prestation}).\n\nConformément à "
                  "l'article L. 441-10 du Code de commerce, cette somme est majorée des pénalités de retard "
                  "au taux légal et d'une indemnité forfaitaire de 40 €.\n\nDélai ultime : 8 jours après "
                  "réception, faute de quoi nous saisirons le tribunal d'une demande d'injonction de payer.\n\n"
                  "Veuillez agréer, Madame, Monsieur, l'expression de nos salutations distinguées.\n{clinique}")
    },
    "J+60": {
        "objet": "Proposition d'échelonnement — Facture n° {facture}",
        "corps": ("Bonjour {prenom} {nom},\n\nMalgré nos relances, la facture n° {facture} ({montant} €) "
                  "demeure impayée. Pour éviter une procédure judiciaire, nous proposons un échelonnement "
                  "en {n} mensualités de {mensualite} € à compter du {date_debut}. Merci de retourner l'accord "
                  "signé sous 8 jours ; à défaut, le dossier sera transmis à un organisme de recouvrement.\n\n"
                  "{clinique}")
    },
}


def main():
    parser = argparse.ArgumentParser(description="App locale de suivi des impayés (vétérinaire)")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default=DEFAULT_DB)
    args = parser.parse_args()

    init_db(args.db, seed=True)
    Handler.api = Api(args.db)
    server = ThreadingHTTPServer((HOST, args.port), Handler)
    print(f"Suivi des impayés — http://{HOST}:{args.port}  (Ctrl+C pour arrêter)")
    print(f"Base de données : {args.db}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt.")


if __name__ == "__main__":
    main()
