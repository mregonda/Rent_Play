from pickle import FALSE
import json
from flask import Flask,request,redirect,url_for,jsonify
from flask_restful import Api,Resource,reqparse
from dbmodels import InstrumentImageDocs, Rating, RenterTransaction, Review, User, db, Instrument, Location, InstrumentOwnerDetails, Coupon, RentedItem, InstrumentRenterDetails
import random
import string
import re
from flask_bcrypt import Bcrypt
import sys
import captcha
from captcha.image import ImageCaptcha
import random,time
import smtplib, ssl
import os
from email.message import EmailMessage
from datetime import datetime
from sqlalchemy import and_
import flask_cors
from flask_cors import CORS,cross_origin
from flask_migrate import Migrate
import owner, instrumentHelper, transaction, customer
app=Flask(__name__)
cors=CORS(app,resource={
    r"/*":{
        "origin":"*"
    }
 })

#CORS(app, supports_credentials=True)

migrate = Migrate(app, db)


#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://axqjhbfdoelshb:5efe6d7f08a40d2e9f9ca4c6599730d3d6bb5c33a526e6d315d270a98e1e7002@ec2-44-207-133-100.compute-1.amazonaws.com:5432/d7349f6c8ptikf' #os.environ['DATABASE_URL']

api=Api(app)
db.init_app(app)
bcrypt=Bcrypt(app)

#@app.before_first_request
#@cross_origin(supports_credentials=True)

def create_Table():
    db.create_all()

class Register(Resource):
    def get(self):             #method='GET'
        userdetail = User.query.all()
        return {"User":list(x.json() for x in userdetail)}
    
    def post(self):             #method='POST'
        user = request.get_json()
        if user['password']==" ":
            sys.stdout('Status: 404 Not Found\r\n\r\n')

        hashed_password=bcrypt.generate_password_hash(user['password']).decode('utf8')
        userdetail = User(user['email'],user['username'],hashed_password,user['role'],user['answer1'],user['answer2'])

        try:
            db.session.add(userdetail)
            db.session.commit()
            db.session.flush()
            db.session.refresh(userdetail)

            if user['role'] == "OWNER":
                newOwnerDetails = InstrumentOwnerDetails("ownerName", userdetail.id)
                db.session.add(newOwnerDetails)
                db.session.commit()
                db.session.flush()
            elif user['role'] == "USER":
                newRenterDetails = InstrumentRenterDetails(userdetail.id)
                db.session.add(newRenterDetails)
                db.session.commit()
                db.session.flush()

            status = 'The user is successfully registered'
            success=True

            return {'result':status,'success':success}, 200
        except:
            status = 'this user is already registered'
            success=False

            return {'result':status,'success':success}, 400
        

class Login(Resource):
    def post(self):           #method='POST'
        json_data = request.get_json()
        print(json_data)
        userdetail = User.query.filter_by(username=json_data['username']).first()
        if not userdetail:
            userdetail = User.query.filter_by(email=json_data['username']).first()
        
        if userdetail and bcrypt.check_password_hash(userdetail.password,json_data['password']):
            print(userdetail)
            print(userdetail.password)
            userID = userdetail.id
            success=True
            return {'message':'Login successful! Welcome '+userdetail.username+'', 'userID':userID, 'role': userdetail.role,'success':success}
        return {'message':'user not found','success':False}, 400

class UsernameGenerator(Resource):
    def get(self,email):
        #First check if email is in correct format
        #Got regex from https://www.c-sharpcorner.com/article/how-to-validate-an-email-address-in-python/
        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$' 
        if(re.search(regex,email)):
            #Get the part of the string before the @ (ex. from "abc@iu.edu", we get "abc")
            emailUsername = email.split("@")[0]

            #Generate 6 random upppercase letters or digits and add this to end of emailUsername
            generated_addOn = ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(6))
            generated_username = emailUsername + generated_addOn

            #Make sure generated_username is not already in database
            exists = User.query.filter_by(username=generated_username).first() is not None

            #Make generation into loop
            while exists:
                #Do random generation again
                generated_addOn = ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(6))
                generated_username = emailUsername + generated_addOn

                #Update exists variable
                exists = User.query.filter_by(username=generated_username).first() is not None
            success=True
            return {'generatedUsername': generated_username, 'success': success}

        else:
            return {'generatedUsername': '','message': 'Invalid email address','success':False}, 400

class SendOTP(Resource):
    def post(self):
        json_data = request.get_json()

        print(json_data)
        json_email = json_data['email']
        userdetail = User.query.filter_by(email=json_email).first()

        if userdetail:
            print(userdetail)

            port = 465  # For SSL
            smtp_server = "smtp.gmail.com"
            sender_email = "forseproject18@gmail.com"  # Enter your address
            password = "CISnnXh7H8X6" #Need to store this somewhere else
            password = "crsbxvyhwshkrmyg"
            receiver_email = json_email  # Enter receiver address
            OTP = random.randint(10000, 99999)

            msg = EmailMessage()
            content = f"Here is your OTP for password reset: {OTP}"
            msg.set_content(content)
            msg['Subject'] = "Rent&Play OTP"
            msg['From'] = sender_email
            msg['To'] = receiver_email

            # Create a secure SSL context
            context = ssl.create_default_context()

            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(sender_email, password)
                server.send_message(msg)

            return {'OTP': OTP, 'message': 'Email address was found, and OTP has been sent.', 'success':True}, 200
        else:
            return {'OTP': None, 'message': 'Email address was not found in database', 'success':False}, 400

class CheckSecurityQuestions(Resource):
    def post(self):
        json_data = request.get_json()

        json_email = json_data['email']
        json_answer1 = json_data['answer1']
        json_answer2 = json_data['answer2']
        userdetail = User.query.filter_by(email=json_email).first()

        if userdetail:
            question1Answer = userdetail.answer1
            question2Answer = userdetail.answer2
            if (json_answer1 == question1Answer) and (json_answer2 == question2Answer):
                return {'message': 'Security questions were correctly given.', 'success':True}, 200
            else:
                return {'message': 'Security questions were incorrect', 'success':False}, 400
        else:
            return {'message': 'User was not found with given email address', 'success':False}, 400

class ResetPassword(Resource):
    def post(self,email):
        try:
            json_data = request.get_json()            
            print(json_data['password'])
            hashed_password=bcrypt.generate_password_hash(json_data['password']).decode('utf8')
            userdetail = User.query.filter_by(email=email).first()
            userdetail.password=hashed_password
           
            db.session.merge(userdetail)
            db.session.flush()
            db.session.commit()
         
            message='Password resetted successfully'
            success=True
        except:
            message='User not found'
            success=False
            
        return {'message': message,"success":success}


global num1
num1=random.randint(1000,9999)
def captcha():
        
    image=ImageCaptcha()
    tstr=time.strftime("%Y%m%d-%H%M%S")
    image.write(str(num1),'./static/'+tstr+'.png')
    return num1,tstr
    

@app.route("/captcha",methods=['GET','POST'])
def index():
    global num1
    num1,tstr= captcha()
    if request.method=='GET':
        return f'''
        <form method="POST">
        <img src="./static/{tstr}.png"><br>
        <input type="text" name="ip">
        <button type="submit">submit</button>
        '''
    elif request.method=='POST':
        ip=request.form["ip"]
        print("code"+ip)
        print(num1)
        try:
            if int(ip)==int(num1):
                return jsonify({'success':True})
            else:
                return redirect(url_for(".index"))
        except:
            return jsonify({'success':False})

class AdminApprovalStatus(Resource):
    def get(self):
        try:
            query = db.session.query(RenterTransaction, RentedItem, Instrument, InstrumentOwnerDetails, InstrumentRenterDetails)\
                        .join(RentedItem, RenterTransaction.id == RentedItem.renterTransactionID)\
                        .join(InstrumentRenterDetails, RenterTransaction.ins_renter_details_id == InstrumentRenterDetails.id)\
                        .join(Instrument, RentedItem.instrumentID == Instrument.id)\
                        .join(InstrumentOwnerDetails, Instrument.ins_owner_details_id == InstrumentOwnerDetails.id)


            #owner name, owner id, renter name.
            query = query.filter(RenterTransaction.approvedStatus==False)
            allDetails = []
            for row in query.all():
                transaction, rentedItem, instrument, ownerDetails, renterDetails = row[0], row[1], row[2], row[3], row[4]
                jsonObject = transaction.json()
                jsonObject.update({"ownerID": ownerDetails.id, "ownerName": ownerDetails.ownerName, "renterID": renterDetails.id})
                allDetails.append(jsonObject)

            return{"Details":allDetails,"success":True},200
        except:
            return{"Details":[], "success":False},400
    def post(self):
        try:
            json_data = request.get_json()
            renterTrans = RenterTransaction.query.filter_by(id=json_data["id"]).first()
            renterTrans.approvedStatus = True

            rentedItems = RentedItem.query.filter_by(renterTransactionID = json_data["id"]).all()

            for item in rentedItems:
                ins = Instrument.query.filter_by(id=item.instrumentID).first()
                ins.isAvailable = False

            db.session.commit()
            return{"success":True},200
        except:
            return{"success":False},400


class GetInstrumentDetails(Resource):
    def post(self):
        try:
            json_data = request.get_json()
            print(json_data)
            query = db.session.query(Instrument, InstrumentOwnerDetails, Location)\
                        .join(InstrumentOwnerDetails, Instrument.ins_owner_details_id == InstrumentOwnerDetails.id)\
                        .join(Location)

            query = query.filter(Instrument.isAvailable==True, Instrument.id == json_data["instrumentID"])
            # print(query)
            # print(query.all())
            queryOutput=query.all()[0]
            print(queryOutput)
            instrument, ownerDetails, location = queryOutput[0],queryOutput[1],queryOutput[2]
            jsonObject = instrument.json() #Initial json data
            
            averageRating = instrumentHelper.get_instrument_average_rating(instrument.id)
            media = instrumentHelper.get_instrument_media(instrument.id)

            jsonObject.update({"averageRating":averageRating, "ownerID":ownerDetails.id, "ownerName":ownerDetails.ownerName, "lat":str(location.lat), "lon":str(location.lon), 'MediaLinks':media})

            return{"instrumentDetails":jsonObject, "success":True},200
        except:
            return{"instrumentdetails":[], "success":False},400

        
class SearchListing(Resource):
    def get(self):             #method='GET'
        try:
            query = db.session.query(Instrument, InstrumentOwnerDetails, Location)\
                        .join(InstrumentOwnerDetails, Instrument.ins_owner_details_id == InstrumentOwnerDetails.id)\
                        .join(Location)

            query = query.filter(Instrument.isAvailable==True)
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


    def post(self):             #method='POST'
        try:
            json_data = request.get_json()

            query = db.session.query(Instrument, InstrumentOwnerDetails, Location)\
                    .join(InstrumentOwnerDetails, Instrument.ins_owner_details_id == InstrumentOwnerDetails.id)\
                    .join(Location)

            query = query.filter(Instrument.instrumentName==json_data['instrument'], Instrument.isAvailable==True)
            searchedInstruments = []
            for row in query:
                instrument, ownerDetails, location = row[0], row[1], row[2]
                jsonObject = instrument.json() #Initial json data

                #Get media and rating for instrument
                averageRating = instrumentHelper.get_instrument_average_rating(instrument.id)
                media = instrumentHelper.get_instrument_media(instrument.id)

                #Add the rest of the json data and append to list
                jsonObject.update({"averageRating":averageRating, "ownerID":ownerDetails.id, "ownerName":ownerDetails.ownerName, "lat":str(location.lat), "lon":str(location.lon), 'MediaLinks':media})
                searchedInstruments.append(jsonObject)

            return {"instruments":searchedInstruments, "success":True}, 200
            
        except:
            return {"instruments":[], "success":False}, 400

class FilterListing(Resource):
    def post(self):
        try:
            json_data = request.get_json()

            instrumentNameInput = json_data['instrumentName']
            instrumentCategoryInput = json_data['instrumentCategory']
            brandNameInput = json_data['brandName']
            priceRangeInput = json_data['priceRange'].split('-') #Format: [50, 75] list from '50-75' string
            ageRangeInput = json_data['ageRange'].split('-') #Format: same as above
            ratingsRangeInput = json_data['ratingsRange'].split('-') #Format: same above
            #distanceRangeInput = json_data['distanceRange'].split('-')

            #Code for is_filled gotten from: https://stackoverflow.com/questions/66016343/flask-sqlalchemy-apply-filter-only-if-value-to-compare-is-not-empty
            def is_filled(raw_data):
                try:
                    value = raw_data[0]
                    if value == '':
                        return False
                except (IndexError, TypeError):
                    return False
                return True

            query = db.session.query(Instrument, InstrumentOwnerDetails, Location)\
                .join(InstrumentOwnerDetails, Instrument.ins_owner_details_id == InstrumentOwnerDetails.id)\
                .join(Location)

            conditions = [Instrument.isAvailable == True]
            if is_filled(instrumentNameInput):
                conditions.append(Instrument.instrumentName == instrumentNameInput)
            if is_filled(instrumentCategoryInput):
                conditions.append(Instrument.instrumentCategory == instrumentCategoryInput)
            if is_filled(brandNameInput):
                conditions.append(Instrument.brandName == brandNameInput)
            if is_filled(priceRangeInput):
                conditions.append(Instrument.price >= float(priceRangeInput[0]))
                conditions.append(Instrument.price <= float(priceRangeInput[1]))
            if is_filled(ageRangeInput):
                conditions.append(Instrument.age >= int(ageRangeInput[0]))
                conditions.append(Instrument.age <= int(ageRangeInput[1]))
            #if is_filled(distanceRangeInput):
                #Check for distance away and add condition

            query = query.filter(and_(*conditions))

            filteredInstruments = []
            for row in query:
                instrument, ownerDetails, location = row[0], row[1], row[2]
                jsonObject = instrument.json()
                averageRating = instrumentHelper.get_instrument_average_rating(instrument.id)
                media = instrumentHelper.get_instrument_media(instrument.id)
                jsonObject.update({"averageRating":averageRating, "ownerID":ownerDetails.id, "ownerName":ownerDetails.ownerName, "lat":str(location.lat), "lon":str(location.lon), 'MediaLinks':media})
                if not (is_filled(ratingsRangeInput)):
                    filteredInstruments.append(jsonObject)
                elif is_filled(ratingsRangeInput) and averageRating >= float(ratingsRangeInput[0]) and averageRating <= float(ratingsRangeInput[1]):
                    filteredInstruments.append(jsonObject)

            return {"instruments":filteredInstruments, "success":True}, 200
        except:
            return {"instruments":[], "success":False}, 400

class AddRating(Resource): 
    def post(self):
        rate = request.get_json()
        
        if(rate['ref_type']=="owner"):
            ratingdetail = Rating(rate['ref_id_owner'], None, rate['ref_type'], rate['rating'])
        elif(rate['ref_type']=='instrument'):
            ratingdetail = Rating(None, rate['ref_id_instrument'], rate['ref_type'], rate['rating'])
        try:
            db.session.add(ratingdetail)
            db.session.commit()
            db.session.flush()
            return {'result':'Rating succesfully inserted', 'success':True}, 200
        except:
            return {'result':'Not inserted', 'success':False}, 400


class GetRatings(Resource):
    def get(self):
        ratingdetail = Rating.query.all()
        return {"Rating":list(x.json() for x in ratingdetail)}

class GetInstrumentRatings(Resource):
    def post(self):
        try:
            json_data = request.get_json()
            ins_id = json_data['instrumentID']
            ratings = Rating.query.filter(Rating.ref_id_instrument == ins_id, Rating.ref_type == "instrument").all()
            return {"ratings": list(x.rating for x in ratings), "success":True}, 200
        except:
            return {"ratings": [], "success":False}, 400


class AddReview(Resource):
    def post(self):
        rev = request.get_json()
        if(rev['ref_type']=="owner"):
            reviewdetail = Review(rev['ref_id_owner'],None,rev['ref_type'],rev['reviewComment'])
        elif(rev['ref_type']=="instrument"):
            reviewdetail = Review(None,rev['ref_id_instrument'],rev['ref_type'],rev['reviewComment'])
        try:
            db.session.add(reviewdetail)
            db.session.commit()
            db.session.flush()
            return {'result':'Review succesfully inserted', 'success':True}, 200
        except:
            return {'result':'Not inserted', 'success':False}, 400

class GetReview(Resource):
    def get(self):
        reviewdetail = Review.query.all()
        return {"Review":list(x.json() for x in reviewdetail)}

class GetInstrumentReviews(Resource):
    def post(self):
        try:
            json_data = request.get_json()
            ins_id = json_data['instrumentID']
            reviews = Review.query.filter(Review.ref_id_instrument == ins_id, Review.ref_type == "instrument").all()
            return {"reviews": list(x.reviewComment for x in reviews),"success":True}, 200
        except:
            return {"reviews": [], "success":False}, 400

class GetLocations(Resource):
    def get(self):
        try:
            locations = Location.query.all()
            return {"Locations":list(x.json() for x in locations)}, 200
        except:
            return {"Locations": None, "status":False}, 400


class GetCustomerRequest(Resource):
    def post(self):
        try:
            json_data = request.get_json()
            instrumentID = json_data['instrumentID']

            rentedItem = RentedItem.query.filter(RentedItem.instrumentID==instrumentID, RentedItem.status==True).one()
            renterTransaction = RenterTransaction.query.filter_by(id=rentedItem.renterTransactionID).one()
            renter = InstrumentRenterDetails.query.filter_by(id=renterTransaction.ins_renter_details_id).one()
            userDetails = User.query.filter_by(id=renter.userID).one()
            location = Location.query.filter_by(ref_id_renter=renter.id).one()

            returnJson = {"email":userDetails.email, "startDate":str(renterTransaction.fromDate), "endDate":str(renterTransaction.toDate), "lat":str(location.lat), "lon":str(location.lon)}

            return {"customerInfo":returnJson, "success":True}, 200
        except:
            return {"customerInfo":None, "success":False}, 400


api.add_resource(Register,'/register')
api.add_resource(Login,'/login')
api.add_resource(UsernameGenerator, '/generateUsername/<string:email>')
api.add_resource(ResetPassword,'/resetpassword/<string:email>')   
api.add_resource(SendOTP, '/sendOTP')
api.add_resource(CheckSecurityQuestions, '/checksecurityquestions')
api.add_resource(SearchListing,'/search')
api.add_resource(FilterListing, '/filterListing')
api.add_resource(AddRating, '/addrating')
api.add_resource(GetRatings, '/getratings')
api.add_resource(GetInstrumentRatings, '/getinstrumentratings')
api.add_resource(AddReview, '/addreview')
api.add_resource(GetReview, '/getreviews')
api.add_resource(GetInstrumentReviews, '/getinstrumentreviews')
api.add_resource(GetLocations, '/getlocations')
api.add_resource(GetInstrumentDetails,'/getinstrumentdetails')
api.add_resource(owner.AddInstrument, '/addinstrument')
api.add_resource(owner.UploadMedia, '/uploadmedia')
api.add_resource(owner.GetOwnerID, '/getownerid')
api.add_resource(AdminApprovalStatus, '/adminapprovalstatus')
api.add_resource(owner.GetAllOwnedInstruments, '/getallownedinstruments')
api.add_resource(transaction.CalculateTotalPrice, '/calculatetotalprice')
api.add_resource(transaction.AddRenterTransaction, '/addrentertransaction')
api.add_resource(transaction.GetCouponDetails, '/getcoupondetails')
api.add_resource(transaction.MakePayment, '/makepayment')
api.add_resource(customer.ViewInstrumentsWaitingApproval, '/viewinstrumentswaitingapproval')
api.add_resource(customer.ViewInstrumentsCurrent, '/viewinstrumentscurrent')
api.add_resource(customer.ViewInstrumentsPast, '/viewinstrumentspast')
api.add_resource(GetCustomerRequest, '/getcustomerrequest')

app.debug = True

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

if __name__=='__main__':
    app.run(hostname='localhost',port=5000)

