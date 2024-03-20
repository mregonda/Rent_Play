from flask import request
from flask_restful import Resource
from dbmodels import Instrument, RentedItem, RenterTransaction, InstrumentRenterDetails, db
import instrumentHelper


class ViewInstrumentsWaitingApproval(Resource):
    def post(self):
        try:
            json_data = request.get_json()
            userID = json_data['userID']
            renter = InstrumentRenterDetails.query.filter_by(userID=userID).first()
            if renter == None:
                return {"message": "This user is not signed up as a renter.", "waitingApprovalInstruments": [], "status": False}, 200

            query = db.session.query(RenterTransaction, RentedItem, Instrument)\
                                                    .join(RentedItem, RentedItem.renterTransactionID == RenterTransaction.id)\
                                                    .join(Instrument, Instrument.id == RentedItem.instrumentID)

            waitingApprovalQuery = query.filter(RenterTransaction.ins_renter_details_id == renter.id,\
                                            RenterTransaction.approvedStatus == False)

            waitingApproval = []
            for row in waitingApprovalQuery.all():
                transaction, rentedItem, instrument = row[0], row[1], row[2]
                json_object = instrument.json()
                media = instrumentHelper.get_instrument_media(instrument.id)
                json_object.update({"transactionID": transaction.id, "fromDate": str(transaction.fromDate), "toDate": str(transaction.toDate), "approvedStatus": transaction.approvedStatus, "isPaid": transaction.isPaid, "status": rentedItem.status, "isAvailable": instrument.isAvailable, "MediaLinks":media})
                waitingApproval.append(json_object)
        
            return {"message": "Returned succesfully", "waitingApprovalInstruments": waitingApproval, "status": True}, 200
        except:
            return {"message": "Error in code", "waitingApprovalInstruments":[], "status":False}, 400


class ViewInstrumentsCurrent(Resource):
    def post(self):
        try:
            json_data = request.get_json()
            userID = json_data['userID']
            renter = InstrumentRenterDetails.query.filter_by(userID=userID).first()
            if renter == None:
                return {"message": "This user is not signed up as a renter.", "currentInstruments": [], "status": False}, 200

            query = db.session.query(RenterTransaction, RentedItem, Instrument)\
                                                    .join(RentedItem, RentedItem.renterTransactionID == RenterTransaction.id)\
                                                    .join(Instrument, Instrument.id == RentedItem.instrumentID)
        
            currentQuery = query.filter(RenterTransaction.ins_renter_details_id == renter.id,\
                                RenterTransaction.approvedStatus == True,\
                                RentedItem.status == True)

            current = []
            for row in currentQuery.all():
                transaction, rentedItem, instrument = row[0], row[1], row[2]
                json_object = instrument.json()
                media = instrumentHelper.get_instrument_media(instrument.id)
                json_object.update({"transactionID": transaction.id, "fromDate": str(transaction.fromDate), "toDate": str(transaction.toDate), "approvedStatus": transaction.approvedStatus, "isPaid": transaction.isPaid, "status": rentedItem.status, "isAvailable": instrument.isAvailable,"MediaLinks":media})
                current.append(json_object)
        
            return {"message": "Returned succesfully", "currentInstruments": current, "status": True}, 200
        except:
            return {"message":"Error in code", "currentInstruments":[], "status": False}, 400
        

class ViewInstrumentsPast(Resource):
    def post(self):
        try:
            json_data = request.get_json()
            userID = json_data['userID']
            renter = InstrumentRenterDetails.query.filter_by(userID=userID).first()
            if renter == None:
                return {"message": "This user is not signed up as a renter.", "pastInstruments": [], "status": False}, 200

            query = db.session.query(RenterTransaction, RentedItem, Instrument)\
                                                    .join(RentedItem, RentedItem.renterTransactionID == RenterTransaction.id)\
                                                    .join(Instrument, Instrument.id == RentedItem.instrumentID)
        
            pastQuery = query.filter(RenterTransaction.ins_renter_details_id == renter.id,\
                                RentedItem.status == False)

            past = []
            for row in pastQuery.all():
                transaction, rentedItem, instrument = row[0], row[1], row[2]
                json_object = instrument.json()
                media = instrumentHelper.get_instrument_media(instrument.id)
                json_object.update({"transactionID": transaction.id, "fromDate": str(transaction.fromDate), "toDate": str(transaction.toDate), "approvedStatus": transaction.approvedStatus, "isPaid": transaction.isPaid, "status":rentedItem.status, "isAvailable": instrument.isAvailable, "MediaLinks":media})
                past.append(json_object)

            return {"message": "Returned succesfully", "pastInstruments": past, "status": True}, 200
        except:
            return {"message":"Error in code", "pastInstruments":[], "status": False}, 400