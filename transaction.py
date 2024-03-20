from flask import request
from flask_restful import Resource
from dbmodels import Instrument, Coupon, RentedItem, RenterTransaction, InstrumentOwnerDetails, InstrumentRenterDetails, User, db
from datetime import datetime
from email.message import EmailMessage
import smtplib, ssl


class CalculateTotalPrice(Resource):
    def post(self):
        json_data = request.get_json()

        listOfInstruments = json_data['listOfIDs']
        couponName = json_data['couponName']

        totalPrice = 0
        for instrumentID in listOfInstruments:
            instrument = Instrument.query.filter_by(id = instrumentID).first()
            totalPrice += instrument.price

        percentOfTotal = 1
        if couponName != '':
            coupon = Coupon.query.filter_by(name = couponName).first()
            if coupon:
                percentOfTotal = 1 - coupon.percentDiscount

        totalPrice *= percentOfTotal
        return {"TotalPrice": round(totalPrice, 2), "success":True}, 200


class AddRenterTransaction(Resource):
    def post(self):
        try:
            json_data = request.get_json()

            listOfInstruments = json_data['listOfIDs']
            userID = json_data['userID']
            totalPrice = json_data['totalPrice']
            fromDate = datetime.strptime(json_data['fromDate'], '%Y-%m-%d')
            toDate = datetime.strptime(json_data['toDate'], '%Y-%m-%d')

            #Check to see if renterID exists. If not, create a new renter.
            renterDetails = InstrumentRenterDetails.query.filter_by(userID=userID).first()
            if renterDetails == None:
                newRenter = InstrumentRenterDetails(userID)
                db.session.add(newRenter)
                db.session.commit()
                db.session.flush()
                db.session.refresh(newRenter)
                renterDetails = newRenter


            #Preliminary check to see if all these instruments are available and not in a different transaction already.
            for instrumentID in listOfInstruments:
                rentedItems = RentedItem.query.filter_by(instrumentID = instrumentID).all()
                
                #Check to see if there are any currently rented items that already have this instrument id
                for item in rentedItems:
                    if item.status == True:
                        return {"message": "Someone is already renting or in the the process of renting one of these instruments", "transactionID": None, "success": False}, 400

                #Change the isAvailable to False for each instrument
                instrument = Instrument.query.filter_by(id = instrumentID).one()
                instrument.isAvailable = False
                db.session.commit()

            newTransaction = RenterTransaction(renterDetails.id, totalPrice, fromDate, toDate, False, False)
            db.session.add(newTransaction)
            db.session.commit()
            db.session.flush()
            db.session.refresh(newTransaction)

            for instrumentID in listOfInstruments:
                newRentedItem = RentedItem(newTransaction.id, instrumentID, True) #Status becomes True, until the instrument is returned.

                db.session.add(newRentedItem)
                db.session.commit()
                db.session.flush()

            return {"message": "The transaction was added", "transactionID": newTransaction.id, "success": True}, 200
        except:
            return {"message": "The transaction could not be added", "transactionID": None, "success": False}, 400

class GetCouponDetails(Resource):
    def post(self):
        try:
            json_data = request.get_json()
            couponName = json_data['couponName']
            couponDetails = Coupon.query.filter_by(name = couponName).first()

            return {"percentDiscount": couponDetails.percentDiscount, "endDate": str(couponDetails.endDate), "success": True}, 200

        except:
            return {"percentDiscount": None, "endDate": None, "success": False}, 400


class MakePayment(Resource):
    def post(self):
        try:
            json_data = request.get_json()
            transactionID = json_data["transactionID"]

            #Update the isPaid column
            transaction = RenterTransaction.query.filter_by(id = transactionID).first()
            if transaction.isPaid == True:
                return {"message":"Transaction has already been paid for.", "status":False}, 200
            transaction.isPaid = True
            db.session.commit()

            #Get the renter emails and send a confirmation
            renter = InstrumentRenterDetails.query.filter_by(id=transaction.ins_renter_details_id).first()
            renterUserDetails = User.query.filter_by(id=renter.userID).first()
            content = "Your payment of " + str(transaction.totalPrice) + "$ was processed. Please return the instruments to all the owners by " + str(transaction.toDate) + ". Thank you."
            sendPaymentEmail(renterUserDetails.email, content)

            #Get the list of owners and send emails for all of them.
            query = db.session.query(RentedItem, Instrument, InstrumentOwnerDetails, User)\
                            .join(Instrument, Instrument.id == RentedItem.instrumentID)\
                            .join(InstrumentOwnerDetails, InstrumentOwnerDetails.id == Instrument.ins_owner_details_id)\
                            .join(User, User.id == InstrumentOwnerDetails.userID)
            
            query = query.filter(RentedItem.renterTransactionID == transaction.id)
            for row in query.all():
                print(row)
                rentedItem, instrument, ownerDetails, userDetails = row[0], row[1], row[2], row[3]
                email = userDetails.email
                content = "A payment was made on your " + instrument.instrumentName + "."
                sendPaymentEmail(email, content)
                                
            return {"message": "The payment has been processed.", "status":True}, 200
        except:
            return {"message": "Error in the code.", "status": False}, 400


def sendPaymentEmail(email, content):
    #Send emails
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "forseproject18@gmail.com"  # Enter your address
    password = "CISnnXh7H8X6" #Need to store this somewhere else
    password = "crsbxvyhwshkrmyg"
    receiver_email = email  # Enter receiver address

    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = "Rent&Play Payment Processed"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.send_message(msg)