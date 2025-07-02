# 6 arrays feeling
colere = ["irritation", "contrariété", "agacement", "impatience", "exaspération", "frustration", "mécontentement", "rancune", "hostilité", "énervement", "colère_sourde", "indignation", "animosité", "rage_contenue", "fureur", "violence_verbale", "emportement", "colère_explosive", "haine", "fureur_destructrice"]
tristesse = ["nostalgie", "mélancolie", "abattement", "langueur", "morosité", "désenchantement", "lassitude", "découragement", "inquiétude_pesante", "blues", "peine", "affliction", "pleurs_silencieux", "désespoir_latent", "tristesse_profonde", "solitude_écrasante", "dépression", "désolation", "désespoir_intense", "vide_existentiel"]
peur = ["inquiétude_légère", "appréhension", "nervosité", "crainte", "gêne", "trac", "méfiance", "stress", "anxiété", "angoisse", "terreur_anticipée", "peur_sourde", "frayeur", "panique_légère", "effroi", "phobie", "détresse", "épouvante", "paranoïa", "terreur_paralysante"]
paix = ["calme", "tranquillité", "repos", "légèreté", "silence_intérieur", "relâchement", "détente", "quiétude", "harmonie", "équilibre", "acceptation", "sérénité_douce", "clarité_mentale", "présence_paisible", "lucidité_tranquille", "confiance_posée", "plénitude", "paix_intérieure", "alignement_profond", "union_spirituelle"]
joie = ["satisfaction", "plaisir", "contentement", "réjouissance", "sourire_intérieur", "léger_enthousiasme", "agréable_surprise", "vivacité", "bonne_humeur", "joie_simple", "éclat_de_rire", "excitation_positive", "jubilation", "fierté", "bonheur_partagé", "euphorie_légère", "bonheur_profond", "ravissement", "extase_joyeuse", "ivresse_du_bonheur"]
serenite = ["apaisement", "zénitude", "allégement", "clarté", "sérénité_discrète", "acceptation_paisible", "présence_calme", "assurance_tranquille", "confiance_paisible", "équanimité", "douceur_intérieure", "stabilité_émotionnelle", "immobilité_sereine", "ancrage", "compassion_paisible", "élan_de_sagesse", "pureté_spirituelle", "sérénité_profonde", "conscience_éveillée", "illumination_paisible"]
feelings = {"Colère":colere, "Tristesse":tristesse, "Peur":peur, "Paix":paix, "Joie":joie, "Sérénité":serenite}

with open("feelings.sms", "w", encoding="iso-8859-1") as f:
    f.write("= Vie =\n")
    for category in feelings:
        f.write(f"->{category}\n")

    for category, emotions in feelings.items():
        f.write(f"\n= {category} =\n")
        f.write(f"->{emotions[0]}\n")

        for i, emotion in enumerate(emotions):
            f.write(f"\n= {emotion} =\n")
            if i < len(emotions) - 1:
                f.write(f"->{emotions[i + 1]}\n")
