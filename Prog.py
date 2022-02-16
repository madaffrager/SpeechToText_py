from pymediainfo import MediaInfo
#Il va nous permettre d'extraire des informations de la vidéo
#tel que le nombre de canaux, débit binaire, fréquence d'échantillonnage
import subprocess
#Nous permet de créer des processus fils 
#On y aura besoin pour éxecuter des commandes shell à travers l'OS
import sys
#Contient des informations système
#On y aura besoin pour récupérer le nom de la vidéo à transcrire/traduire
import os 
#Module qui nous permet d'interagir avec l'OS
from google.cloud import speech
#On importe le module du speech to text
import boto3
#On commence par importer le module python "boto3" qui contient l'SDK d'AWS


video_filepath = sys.argv[1]
#On définit l'emplacement de la vidéo qui est le 1er argument donné en entrée

dir = video_filepath
name = dir.rsplit('.', 1)[0]
#On va extraire le nom du fichier sans extension

audio_filepath = "Audios/"+name+".mp3"
destination_dir = "Parties/"+name
transcription_file = "Transcription/"+name+".txt"
translation_file = "Traduction/"+name+"_traduit.txt"
#On définiti les différents chemin où on va mettre les audios,
#les petites parties des audios, de transcription et traduction

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'Speech_Text_Key.json'
#On définit une variable d'environement avec le chemin vers le fichier contenant les informations sur notre clé privée

LangageSource = 'auto'
LangageCible = 'en'
#On définit le langage source et le langage cible

media_info = MediaInfo.parse(video_filepath)
#On parcourt le fichier vidéo afin d'extraire les informations nécessaires
os.mkdir(destination_dir)
#On crée un sous dossier dans "Parties" avec le nom de la vidéo


for track in media_info.tracks:
	if track.track_type == "Audio":
		channels=track.channel_s
		bit_rate=track.bit_rate
		sample_rate=track.sampling_rate
	elif track.track_type == "Video":
		duration=track.duration
#On va extraire les informations nécessaires à la ère étape dite "PREPROCESSING"


command = f"ffmpeg -i {video_filepath} -b:a {bit_rate} -ac {channels} -ar {sample_rate} -vn {audio_filepath}"
subprocess.call(command, shell=True)
command2 = f"ffmpeg -i {audio_filepath} -f segment -segment_time 30 -c copy {destination_dir}/partie%05d.mp3"
subprocess.call(command2, shell=True)
#On va extraire le fichier audio depuis la video en utilisant l'ffmpeg et en lui fournissant les informations
#de cannaux, débit et fréquence d'échantillage
#Ensuite, on va découper le fichier audio en des segments de 30 secondes


client = speech.SpeechClient()
#On instancie le client speech to text 


i=1
f1=open(transcription_file, "w")
#On ouvre le fichier de transcription en écriture


for split_audio in os.listdir(destination_dir): #Pour chaque fichier audio dans "Parties/nomVid"
    with open(os.path.join(destination_dir, split_audio), 'rb') as f:
        content = f.read()
    #On lit le contenu de l'audio    
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
            sample_rate_hertz=int(sample_rate),
            audio_channel_count=int(channels),            
            enable_automatic_punctuation=True,
            model='default',
            language_code='fr-FR')
    response = client.recognize(config=config,audio=audio)
    #On envoi les parametres de configuration ainsi que le contenu de l 'audio à l'API

    for result in response.results:        
        f1.write(str(i)+' ===> '+result.alternatives[0].transcript+'\n')
        i+=1
    #Pour chaque résultat retourné par l'API, on l'écrit sur le fichier text de transcription    
f1.close

print('Transcription réussie :-)')

with open(transcription_file, 'rt', encoding='utf-8') as f1:
    contenuFichierSource = f1.read()
#On récupère le contenu du fichier de transcription dans "contenuFichierSource"
#le "Translate web API" a besoin d'un texte encodé en utf-8 

traduction = boto3.client(service_name='translate', region_name='us-east-1', use_ssl=True)
#"boto3" offre plusieurs manières pour pouvoir communiquer avec les services web d'AWS, on utilise ici "client"
#les ressources dont on aura besoin sont le nom du service web, la région et le type de chiffrement
#le service appelé est le service de traduction 'translate'
#la région choisie est celle d'us-east-1
#l'SSL est activé pour sécuriser les communications réseau entre le client et le service aws

resultat = traduction.translate_text(Text=contenuFichierSource , SourceLanguageCode=LangageSource, TargetLanguageCode=LangageCible)
#on fait appel à l'opération 'translate_text' en fournissant le texte qu'on veut traduire, le langage source et le langage cible

contenuFichierDestination = resultat.get('TranslatedText')
#on récupère le texte traduit dans une variable

with open(translation_file, 'wt', encoding='utf-8') as f2:
    f2.write(contenuFichierDestination)
#On écrit le contenu traduit dans un fichier encodé en utf-8

print('La traduction a réussi :-)')