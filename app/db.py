"""Schéma SQLite et données de départ pour l'app de suivi des impayés."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    nom TEXT NOT NULL,
    prenom TEXT DEFAULT '',
    telephone TEXT DEFAULT '',
    email TEXT DEFAULT '',
    adresse TEXT DEFAULT '',
    code_postal TEXT DEFAULT '',
    ville TEXT DEFAULT '',
    consentement_relance INTEGER DEFAULT 0,
    canal_prefere TEXT DEFAULT 'Email',
    mode_paiement TEXT DEFAULT 'CB',
    statut TEXT DEFAULT 'Actif'
);

CREATE TABLE IF NOT EXISTS animaux (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    nom TEXT NOT NULL,
    espece TEXT DEFAULT '',
    race TEXT DEFAULT '',
    sexe TEXT DEFAULT '',
    date_naissance TEXT DEFAULT '',
    numero_puce TEXT DEFAULT '',
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS factures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE NOT NULL,
    date_facture TEXT NOT NULL,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    animal_id INTEGER REFERENCES animaux(id),
    prestation TEXT DEFAULT '',
    categorie TEXT DEFAULT 'Autre',
    montant_ht REAL NOT NULL DEFAULT 0,
    tva_pct REAL NOT NULL DEFAULT 10,
    acompte REAL NOT NULL DEFAULT 0,
    date_echeance TEXT NOT NULL,
    statut TEXT NOT NULL DEFAULT 'Impayée'
);

CREATE TABLE IF NOT EXISTS paiements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    facture_id INTEGER NOT NULL REFERENCES factures(id) ON DELETE CASCADE,
    montant REAL NOT NULL,
    moyen TEXT DEFAULT 'CB',
    reference TEXT DEFAULT '',
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS impayes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    facture_id INTEGER UNIQUE NOT NULL REFERENCES factures(id) ON DELETE CASCADE,
    niveau_relance TEXT DEFAULT 'Aucun',
    prochaine_action TEXT DEFAULT '',
    statut TEXT DEFAULT 'Ouvert',
    responsable TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS relances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    impaye_id INTEGER NOT NULL REFERENCES impayes(id) ON DELETE CASCADE,
    canal TEXT DEFAULT 'Email',
    effectuee_par TEXT DEFAULT '',
    contact TEXT DEFAULT '',
    resume TEXT DEFAULT '',
    reponse_client TEXT DEFAULT 'Aucune',
    date_promesse TEXT DEFAULT '',
    resultat TEXT DEFAULT 'À relancer'
);

CREATE INDEX IF NOT EXISTS idx_factures_client ON factures(client_id);
CREATE INDEX IF NOT EXISTS idx_factures_statut ON factures(statut);
CREATE INDEX IF NOT EXISTS idx_impayes_statut ON impayes(statut);
CREATE INDEX IF NOT EXISTS idx_relances_impaye ON relances(impaye_id);
"""

SEED = """
INSERT INTO clients (code, nom, prenom, telephone, email, adresse, code_postal, ville, consentement_relance, canal_prefere, mode_paiement, statut) VALUES
('CLI-001','Dupont','Marie','0601020304','marie.dupont@example.fr','12 rue des Lilas','75011','Paris',1,'Email','CB','Actif'),
('CLI-002','Martin','Lucas','0612345678','lucas.martin@example.fr','3 avenue de la République','69003','Lyon',1,'SMS','Virement','Actif'),
('CLI-003','Bernard','Sophie','0623456789','sophie.bernard@example.fr','45 chemin des Vignes','33000','Bordeaux',1,'Courrier','Chèque','Actif'),
('CLI-004','Petit','Hugo','0634567890','hugo.petit@example.fr','8 impasse du Moulin','44000','Nantes',0,'Email','CB','Actif'),
('CLI-005','Robert','Emma','0645678901','emma.robert@example.fr','27 boulevard Saint-Michel','31000','Toulouse',1,'Email','CB','Litige');

INSERT INTO animaux (code, nom, espece, race, sexe, date_naissance, numero_puce, client_id) VALUES
('ANI-001','Rex','Chien','Labrador','M','2019-05-12','250268500123456',1),
('ANI-002','Mlya','Chat','Européen','F stérilisée','2021-03-02','250268500654321',1),
('ANI-003','Cookie','Chien','Berger Australien','M','2018-11-20','250268500789012',2),
('ANI-004','Nougat','Chat','Siamois','M','2020-07-15','250268500345678',3),
('ANI-005','Tornado','Cheval','Pur-sang arabe','M','2015-04-01','250268500901234',4),
('ANI-006','Luna','Chien','Beagle','F','2022-01-25','250268500567890',5);

INSERT INTO factures (numero, date_facture, client_id, animal_id, prestation, categorie, montant_ht, tva_pct, acompte, date_echeance, statut) VALUES
('FAC-2026-0001','2026-10-05',1,1,'Consultation + vaccination CHPPI','Consultation',80.00,10,0,'2026-11-04','Impayée'),
('FAC-2026-0002','2026-10-12',2,3,'Chirurgie — stérilisation','Chirurgie',320.00,10,100,'2026-11-11','Partielle'),
('FAC-2026-0003','2026-09-20',3,4,'Consultation + analyses sanguines','Analyses',150.00,10,0,'2026-10-20','Impayée'),
('FAC-2026-0004','2026-10-25',4,5,'Consultation annuelle équine','Consultation',60.00,10,60,'2026-11-24','Payée'),
('FAC-2026-0005','2026-08-15',5,6,'Hospitalisation 3 jours + perfusion','Hospitalisation',890.00,10,0,'2026-09-14','Impayée'),
('FAC-2026-0006','2026-11-01',1,2,'Aliments thérapeutiques renal 12 kg','Alimentation',110.00,20,0,'2026-12-01','À échoir');

INSERT INTO paiements (date, facture_id, montant, moyen, reference, notes) VALUES
('2026-10-26',4,60.00,'CB','','Paiement intégral à la caisse'),
('2026-10-14',2,100.00,'Virement','VR-88412','Acompte à la réservation de la chirurgie');

INSERT INTO impayes (code, facture_id, niveau_relance, prochaine_action, statut, responsable) VALUES
('IMP-001',1,'J+15','Email J+15 + SMS','Ouvert','Secrétariat'),
('IMP-002',2,'J+7','Email J+7','En cours','Secrétariat'),
('IMP-003',3,'J+30','Mise en demeure LRAR','Ouvert','Gérant'),
('IMP-004',5,'J+60','Échelonnement ou injonction de payer','Recouvrement externe','Gérant');

INSERT INTO relances (date, impaye_id, canal, effectuee_par, contact, resume, reponse_client, date_promesse, resultat) VALUES
('2026-11-11',1,'Email','Secrétariat A.','Mme Dupont','Relance J+7 envoyée, facture 88 €','Promesse de payer','2026-11-18','En attente'),
('2026-11-12',2,'SMS','Secrétariat A.','M. Martin','SMS J+7 envoyé, reste 252 €','Aucune','','À relancer'),
('2026-10-27',3,'Email','Secrétariat B.','Mme Bernard','Relance J+7, facture 165 €','Aucune','','Escalader'),
('2026-11-05',3,'Téléphone','Gérant','Mme Bernard','Appel : conteste le montant des analyses','Contestation','','Escalader'),
('2026-09-22',4,'Email','Gérant','Auto-répondeur','Relance J+7, facture 979 €','Aucune','','À relancer'),
('2026-10-15',4,'LRAR','Gérant','Accusé de réception reçu','Mise en demeure envoyée le 15/10','Aucune','','Escalader');
"""


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path, seed=True):
    conn = connect(db_path)
    conn.executescript(SCHEMA)
    if seed:
        count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        if count == 0:
            conn.executescript(SEED)
    conn.commit()
    return conn
