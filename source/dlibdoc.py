import streamlit as st

st.header("Documentation - DLiBdoc")

st.markdown("## Avant-propos")

st.markdown("Le présent document fait office de manuel de mise en œuvre et d'utilisation du système DLiBd 0. " \
"Il décrit le fonctionnement du prototype construit au printemps 2026 à la Direction Recherche et Innovation de la mairie de Rosny-sous-Bois. " \
"Une version DLiBd 1, plus sûre, plus maintenable et plus appropriée à l'insertion du système dans un futur bâtiment est prévue pour décembre 2026. \n" \
"Pour toute information complémentaire, contactez-moi à l'adresse benjamin.to@etu.utc.fr.")

st.markdown("## Introduction")

st.markdown("### Raison d'être")

st.markdown("Le projet Donnée libre pour le bâtiment durable, abrégé DLiBd, est né d'une grande insatisfaction quant aux " \
"systèmes de GTB classiques. La Direction Recherche et Innovation de la mairie de Rosny-sous-Bois en a installé dans chacune " \
"des éco-écoles et des centres de loisirs qu'elle a construits ; or, de très nombreux problèmes les rendent en pratique inutilisables. " \
"Pour résoudre ces problèmes, le service est dépendant des entreprises (privées) qui ont installé ces systèmes et de celles " \
"qui sont propriétaires du matériel. En effet, la connaissance de l'installation est très maigre à cause de la maigreur de la documention" \
"disponible, renforcée par les explications floues des professionnels qui semblent essayer de garder leur savoir jalousement.\n" \
"Conséquences : données indisponibles, inaccessibles, impossible à traiter, impossibilité de remplacer des composants, " \
"maintenance pratiquement impossible, délais d'intervention longs, coûts financiers élevés.")

st.markdown("""
            Plus concrètement, les problèmes suivants ont été rencontrés :
            - Impossibilité de paramétrer le micro-ordinateur central sans logiciel payant spécifique, ce qui aurait permis de corriger des problèmes simples (avec un redémarrage par exemple)
            - Impossibilité d'accéder à certaines fonctionnalités sans avoir un compte avec les privilèges administrateur, ce qui permettrait de corriger des problèmes simples comme activer l'enregistrement des données
            - Les micro-contrôleurs ne se mettent jamais à jour, et les formats des exports en CSV changent fortement entre les versions, ce qui rend complexe le traitement des données
            - Impossibilité de lire d'anciennes sauvegardes sans logiciel payant car fichiers chiffrés
            - Un autre logiciel payant (le superviseur) est devenu obsolète après une mise à jour de l'infrastructure informatique de la mairie
            - Les données ne sont pas toujours enregistrées ou se suppriment automatiquement après un certain délai non modifiable sans droits admin
            - Erreurs dans les dates d'enregistrement (plusieurs jours de retards, heures incorrectes, deux données pour un même instants)
            - Dépenses d'importantes sommes pour mots de passe perdus, pour découvrir ensuite une application non fonctionnelle
            - Perte totale de données sur un bâtiment suite à une surchauffe et un redémarrage raté
            - Adresse IP pour la connexion en local sur le micro-ordinateur non renseignée (X.X.1.140, information renseignée nulle part)
            - etc.
            """)

st.markdown("La précédente énumération non exhaustive justifie de nombreuses interventions des professionnels, sans aucune approche " \
"autonome envisageable. La GTB traditionnelle est une boîte noire destinée à le rester à part pour quelques " \
"spécialistes aux horaires restreints et à la facture facile. \nAlors, pourquoi dépendre d'un système informatique instable, " \
"incompréhensible et privé dans des bâtiments publics ? Pourquoi ne pas construire une GTB open-source et low-tech ?")

st.markdown("### Licence et valeurs")

st.markdown("DLiBd est un système open-source. L'entièreté des technologies et des langages de programmation utilisées le sont aussi. " \
"Le code est écrit de telle sorte à être le plus accessible possible, tout comme le fonctionnement est expliqué de manière à favoriser la contribution " \
"collective et la reproduction pour d'autres projets. \nLe travail présenté est soumis à la licence publique générale GNU (GPL). " \
"L'outil DLiBd est un projet de recherche mené au sein d'une entité publique. La réutilisation, la modification " \
"et la distribution sont autorisées et même encouragées, à la seule condition que tout travail délivré fondé sur DLiBd soit également open-source. Il est formellement interdit " \
"de rendre un produit dérivé propriétaire. La mention de l'auteur initial n'est pas obligatoire. \nLa documentation est rédigée en français. En revanche, les commentaires dans les scripts sont écrits en anglais.")

st.markdown("### Schéma de principe")

st.markdown("Les composantes du dispositif, les techniques et les langages de programmation employés sont résumés sur le schéma suivant.")

st.markdown("## Matériel utilisé")

st.markdown("### Sondes")

st.markdown("Les tests sont réalisés avec des sondes Produal relevant le CO2 et la température. Il est évidemment tout à fait envisageable " \
"d'utiliser d'autres capteurs sous réserve d'adaptation du code. En effet, ces sondes ont les caractéristiques suivantes :")
st.markdown("""
            - Communication en Modbus RTU (RS485)
            - Alimentation en 24V
            - Registres de maintien CO2 et température aux adresses mémoire xx30001 et xx30002
            - Aucune vérification par bit de parité
            - 1 bit de fin
            - Vitesse de transmission (baudrate) de 9600 bits/s
""")
st.markdown("Les spécificités du produit sont à retrouver dans sa notice. Pour des conditions similaires à celles du prototypage, " \
"il suffit de modifier quelques paramètres exposés comme variables dans le fichier reading_sensor.py. Pour permettre la combinaison de sondes de " \
"modèles potentiellement différents et de compteurs, le support multi-plateformes sera à envisager.")
st.markdown("Pour le prototype réalisé à la mairie de Rosny-sous-Bois, les sondes sont sous tension en parallèle sur un transformateur.")

st.markdown("### Micro-ordinateurs")

st.markdown("Chaque bâtiment héberge une machine centrale chargée de communiquer avec les sondes, d'enregistrer les données et de répondre aux " \
"requêtes de l'ordinateur invité. En règle générale, un micro-ordinateur avec 4 Go de RAM suffit. En l'occurence, il s'agit de Raspberry " \
"Pi 4 avec RaspPi OS choisies parce qu'elles sont faciles à configurer, à transporter, à relier à d'autres composants et parce que le système d'exploitation est " \
"construit sur le noyau Linux, un kernel open-source. \nPar défaut, Python et deux interpréteurs sont installés sur la machine. " \
"Pour travailler correctement, un environnement virtuel doit être créé. Il est également conseillé d'installer un navigateur " \
"de base de données (type DB Browser SQLite, avec la commande snap).\nEn conditions réelles, la machine devra être protégée contre les hautes températures d'une " \
"chaufferie, contre l'humidité et contre les potentiels chocs.")
st.markdown("""
            La configuration de base de la Raspberry Pi consiste en :
            - L'installation du système d'exploitation
            - L'activation du SSH pour le débogage
            - La création d'un environnement virtuel DLibD-venv
            - L'installation par pip des librairies Python requises
            - L'installation du service mosquitto ?
            """)
st.markdown("**Installation de l'OS et mise à jour** : connecter une carte SD vierge à un autre ordinateur et installer Raspberry Pi Os (voir " \
"https://www.raspberrypi.com/software/). Insérer la carte dans la RPi, définir les paramètres standards. L'identifiant et le mot de passe " \
"de l'utilisateur root standard (dri par exemple) ont été notés à un endroit approprié. Lancer les commandes sudo apt update et sudo apt upgrade pour mettre à jour la machine.")
st.markdown("**Activation de l'interface VNC pour débogage** : dans les paramètres de la Raspberry. Pour l'ordinateur à distance, utiliser un logiciel comme Tiger VNC.")
st.markdown("**Installation de DB Browser for SQLite** : voir site internet officiel. Le téléchargement par snap est une technique possible (sudo apt install snap puis " \
"snap install sqlitebrowser).")
st.markdown("**Création d'un environnement virtuel** : exécuter python -m venv dlibd-venv pour la création puis source dlibd-venv/bin/activate. " \
"Dans l'éditeur de code (Geanny ou Thonny), configurer l'interpréteur pour utiliser dlibd-venv/bin/python3.")
st.markdown("**Librairies Python** : librairies à installer en pip : paho.mqtt, pymodbus, pyserial.")
st.markdown("**Paramétrage du broker mosquitto** : à réaliser uniquement sur la Raspberry agent ! Pour installer les services, lancer sudo apt install -y mosquitto " \
"mosquitto-clients. La commande sudo systemctl enable mosquitto.service permet de s'assurer que le service sera démarré automatiquement en même temps que la Raspberry. " \
"Pour la configuration de l'authentification, il faut d'abord créer un fichier contenant les identifiants et les mots de passe hashés : sudo mosquitto_passwd " \
"-c etc/mosquitto/passwd dri puis renseigner le mot de passe approprié. Par sécurité, restreindre entièrement les droits aux utilisateurs non-root avec la commande " \
"sudo chmod 700 /etc/mosquitto/passwd. La configuration du broker intervient ensuite dans le fichier /etc/mosquitto/mosquitto.conf.")

st.markdown("De plus, plusieurs fichiers contenant des informations spécifiques à chaque appareil doivent être modifiés. La base de données SQLite " \
"available_sensors.db recense l'ensemble des capteurs disponibles (voir plus bas). L'image sensors_location.png est un plan de localisation" \
"des capteurs.")

st.markdown("### Réseau et ordinateur invité")

st.markdown("Les Raspberries des différents bâtiments appartiennent à un réseau informatique commun. Il peut-être physiquement isolé ou exister " \
"comme un sous-réseau par un VLAN dédié sur un réseau plus large. Pour des maquettes à petite échelle, le réseau peut être constitué à l'aide " \
"d'un switch simple et d'un serveur DHCP. En effet, l'assignation des adresses IP ne se fait pas sans routeur, dans lequel un serveur DHCP " \
"est habituellement intégré. Une application appropriée doit alors être installée sur une des machines du réseau (par exemple, la Raspberry " \
"sur laquelle tourne le broker MQTT - voir section 3.2).\nOn appelle ordinateur invité la machine de l'utilisateur sur laquelle l'application de " \
"visualisation DLiBd est installée. Pour fonctionner correctement, cet appareil doit être connecté au même réseau que l'ensemble des " \
"micro-ordinateurs.")

st.markdown("## Code et interfaces")
st.markdown("Cette section détaille les interactions entre les différentes composantes du système.")

st.markdown("### Communication sondes/micro-ordinateur")

st.markdown("L'essentiel du code concernant cette connexion se trouve dans le fichier reading_sensor.py.\nLa situation précise de prototypage est " \
"ici considérée, c'est-à-dire que les capteurs utilisent le protocole Modbus RTU. Le code du fichier cité précédemment doit être retravaillé " \
"pour des cas différents.")