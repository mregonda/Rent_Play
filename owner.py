from flask import request
from flask_restful import Resource
from dbmodels import Instrument, InstrumentImageDocs, InstrumentOwnerDetails, Location, db
import os
from werkzeug.utils import secure_filename
from googleapiclient.http import MediaFileUpload
from serviceCreate import Create_Service
import instrumentHelper

folder_id = '1zlc9IkstQ45jj4nUKh_pgh4FhffgcnUC'

CLIENT_SECRET_FILE = 'se-project-368622-8580d465dc2c.json'
CLIENT_SECRET_FILE = 'client_secret_141634984886-2nok10ap5bj2ndhlqeiuhjelel1kn0u5.apps.googleusercontent.com.json'
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ["https://www.googleapis.com/auth/drive"]

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

class UploadMedia(Resource):
    def post(self):
        if 'mediaFile' not in request.files:
            return {'result': 'No file part', 'mediaLink':None}, 400
        mediaFile = request.files['mediaFile']
        if mediaFile.filename == '':
            return {'result': 'No selected file', 'mediaLink':None}, 400
        if mediaFile: #and allowed_file()
            filename = secure_filename(mediaFile.filename)

            mediaFile.save(filename)
        
            file_metadata = {'name': filename, 'parents': [folder_id]}
            media = MediaFileUpload(filename)
            gfile = service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='webViewLink, id',
                                        supportsAllDrives=True).execute()

            webViewLink = gfile.get('webViewLink')
            fileID = gfile.get('id')

            print(webViewLink)
            print(fileID)

            media = None
            mediaFile.close()
            os.remove(filename)

            mediaLinkSplit = webViewLink.split("/")
            newLink = "http://drive.google.com/uc?export=view&id=" + str(mediaLinkSplit[5])
            return {'result': 'File uploaded', 'mediaLink':newLink}, 200

class AddInstrument(Resource):
    def post(self):
        json_data = request.get_json()

        #ins_owner_details_id, instrumentName, instrumentCategory, brandName, price, age, isAvailable
        newInstrument = Instrument(json_data['instrumentOwnerID'], json_data['instrumentName'], json_data['instrumentCategory'], json_data['brandName'], json_data['price'], json_data['age'], json_data['isAvailable'])

        try:
            db.session.add(newInstrument)
            db.session.commit()
            db.session.flush()
            db.session.refresh(newInstrument)

            mediaLinkObjects = json_data['mediaLinks']
            imageCount = 0
            for mediaLinkObject in mediaLinkObjects:
                mediaLink = mediaLinkObject['mediaLink']
                isDefault = True if imageCount == 0 else False
                mediaType = mediaLinkObject['mediaType']
                if mediaType == 'image':
                    imageCount += 1 
                newImageDoc = InstrumentImageDocs(newInstrument.id, mediaLink, isDefault, mediaType)
                db.session.add(newImageDoc)
                db.session.commit()
                db.session.flush()

            return {'result':'Instrument succesfully inserted', 'success':True}, 200
        except:
            return {'result':'Instrument could not be inserted', 'success':False}, 400
        
class GetOwnerID(Resource):
    def post(self):
        json_data = request.get_json()

        query = db.session.query(InstrumentOwnerDetails).filter(InstrumentOwnerDetails.userID == json_data['userID'])

        owner = query.first()
        if owner is not None:
            return {'result':'Owner ID found', 'instrumentOwnerID':owner.id, 'success':True}, 200
        else:
            return {'result':'There was no owner found with that user ID.', 'instrumentOwnerID': -1, 'success':False}, 400
        

class GetAllOwnedInstruments(Resource):
    def post(self):
        try:
            ownerID = request.get_json()['ownerID']

            query = db.session.query(Instrument, InstrumentOwnerDetails, Location)\
                        .join(InstrumentOwnerDetails, Instrument.ins_owner_details_id == InstrumentOwnerDetails.id)\
                        .join(Location)

            query = query.filter(Instrument.ins_owner_details_id==ownerID) #Instrument.isAvailable==True, 
            allInstruments = []
            for row in query:
                    instrument, ownerDetails, location = row[0], row[1], row[2]
                    jsonObject = instrument.json() #Initial json data

                    #Get media and rating for instrument
                    averageRating = instrumentHelper.get_instrument_average_rating(instrument.id)
                    media = instrumentHelper.get_instrument_media(instrument.id)

                    #Add the rest of the json data and append to list
                    jsonObject.update({"averageRating":averageRating, "ownerID":ownerDetails.id, "ownerName":ownerDetails.ownerName, "lat":str(location.lat), "lon":str(location.lon), 'MediaLinks':media})
                    allInstruments.append(jsonObject)
            
            return {"instruments":allInstruments, "success":True}, 200
        
        except:
            return {"instruments":[], "success":False}, 400