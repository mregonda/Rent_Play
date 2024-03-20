from multiprocessing.dummy import active_children
from weakref import ref
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'userdetails'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100),unique=True,nullable=False)
    username = db.Column(db.String(80),unique=True,nullable=False)
    password = db.Column(db.String(100))
    role = db.Column(db.String(80),nullable=False)
    answer1 = db.Column(db.String(100),nullable=False) #Security question 1 answer
    answer2 = db.Column(db.String(100),nullable=False) #Security question 2 answer
    
    def __init__(self, email, username, password, role, answer1, answer2):
        self.email = email
        self.username = username
        self.password = password
        self.role = role
        self.answer1 = answer1
        self.answer2 = answer2

    def json(self):
        return {"id":self.id, "email":self.email, "username": self.username, "password": str(self.password), "role":self.role, "answer1":self.answer1, "answer2":self.answer2}


class Instrument(db.Model):
    __tablename__ = 'instrumentdetails'
    id = db.Column(db.Integer, primary_key=True)
    instrumentName = db.Column(db.String(80), nullable=False)
    instrumentCategory = db.Column(db.String(80), nullable=False)
    brandName = db.Column(db.String(80))
    price = db.Column(db.Float(2), nullable=False)
    age = db.Column(db.Integer) #In days
    isAvailable = db.Column(db.Boolean, nullable=False)

    #Connection to InstrumentOwnerDetails
    ins_owner_details_id = db.Column(db.Integer, db.ForeignKey('instrumentownerdetails.id'))
    owner = db.relationship("InstrumentOwnerDetails", back_populates='instruments')

    #Connection to InstrumentImageDocs
    imageDocs = db.relationship("InstrumentImageDocs", back_populates='instrument')

    def __init__(self, ins_owner_details_id, instrumentName, instrumentCategory, brandName, price, age, isAvailable):
        self.ins_owner_details_id = ins_owner_details_id
        self.instrumentName = instrumentName
        self.instrumentCategory = instrumentCategory
        self.brandName = brandName
        self.price = price
        self.age = age
        self.isAvailable = isAvailable

    def json(self):
        return {"id":self.id, "ins_owner_details_id":self.ins_owner_details_id, "instrumentName":self.instrumentName, "instrumentCategory":self.instrumentCategory, "brandName":self.brandName, "price":self.price, "age":self.age, "isAvailable":self.isAvailable}


class InstrumentImageDocs(db.Model):
    __tablename__ = 'instrumentimagedocs'
    id = db.Column(db.Integer, primary_key=True)
    mediaLink = db.Column(db.String(200), nullable=False)
    isDefault = db.Column(db.Boolean, nullable=False)
    mediaType = db.Column(db.String(20)) #Either 'image' or 'video'

    #Connection to Instrument
    instrumentID = db.Column(db.Integer, db.ForeignKey('instrumentdetails.id'))
    instrument = db.relationship("Instrument", back_populates='imageDocs')

    def __init__(self, instrumentID, mediaLink, isDefault, mediaType):
        self.instrumentID = instrumentID
        self.mediaLink = mediaLink
        self.isDefault = isDefault
        self.mediaType = mediaType

    def json(self):
        return {"id":self.id, "instrumentID":self.instrumentID, "mediaLink":self.mediaLink, "isDefault":self.isDefault, "mediaType":self.mediaType}


class InstrumentOwnerDetails(db.Model):
    __tablename__ = 'instrumentownerdetails'
    id = db.Column(db.Integer, primary_key=True)
    ownerName = db.Column(db.String(100), nullable=False)

    #Connection to User table
    userID = db.Column(db.Integer, db.ForeignKey('userdetails.id'))
    user = db.relationship("User")

    #Connection to Instrument table
    instruments = db.relationship("Instrument", back_populates="owner")

    def __init__(self, ownerName, userID):
        self.ownerName = ownerName
        self.userID = userID

    def json(self):
        return {"id":self.id, "ownerName":self.ownerName, "userID":self.userID}

class InstrumentRenterDetails(db.Model):
    __tablename__ = 'instrumentrenterdetails'
    id = db.Column(db.Integer, primary_key=True)

    #Connection to User table
    userID = db.Column(db.Integer, db.ForeignKey('userdetails.id'))
    user = db.relationship("User")

    #Connection to RenterTransaction
    transactions = db.relationship("RenterTransaction", back_populates="renter")

    def __init__(self, userID):
        self.userID = userID

    def json(self):
        return {"id":self.id, "userID":self.userID}


class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True)
    ref_id_owner = db.Column(db.Integer, db.ForeignKey("instrumentownerdetails.id"), nullable=True)
    ref_id_renter = db.Column(db.Integer, db.ForeignKey("instrumentrenterdetails.id"), nullable=True)
    refType = db.Column(db.String(100), nullable=False) #$Right now should be "owner" or "renter".
    lat = db.Column(db.Numeric(20), nullable=False)
    lon = db.Column(db.Numeric(20), nullable=False)


    @hybrid_property
    def ref_id(self):
        return self.ref_id_owner or self.ref_id_renter

    #onwer = db.relationship("InstrumentOwnerDetails")

    def __init__(self, ref_id_owner, ref_id_renter, refType, lat, lon):
        self.ref_id_owner = ref_id_owner
        self.ref_id_renter = ref_id_renter
        self.refType = refType
        self.lat = lat
        self.lon = lon

    def json(self):
        return {"id":self.id, "ref_id":self.ref_id, "refType":self.refType, "lat":str(self.lat), "lon":str(self.lon)}


class Rating(db.Model):
    __tablename__ = "rating"
    id = db.Column(db.Integer, primary_key=True)
    ref_id_owner = db.Column(db.Integer, db.ForeignKey("instrumentownerdetails.id"), nullable=True)
    ref_id_instrument = db.Column(db.Integer, db.ForeignKey("instrumentdetails.id"), nullable=True)
    ref_type = db.Column(db.String, nullable=False) #Should be either "owner" or "instrument"
    rating = db.Column(db.Float, nullable=False)

    @hybrid_property
    def ref_id(self):
        return self.ref_id_owner or self.ref_id_instrument

    def __init__(self, ref_id_owner, ref_id_instrument, ref_type, rating):
        self.ref_id_owner = ref_id_owner
        self.ref_id_instrument = ref_id_instrument
        self.ref_type = ref_type
        self.rating = rating

    def json(self):
        return {"id":self.id, "ref_id":self.ref_id, "ref_type":self.ref_type, "rating":self.rating}


class Review(db.Model):
    __tablename__ = "review"
    id = db.Column(db.Integer, primary_key=True)
    ref_id_owner = db.Column(db.Integer, db.ForeignKey("instrumentownerdetails.id"), nullable=True)
    ref_id_instrument = db.Column(db.Integer, db.ForeignKey("instrumentdetails.id"), nullable=True)
    ref_type = db.Column(db.String, nullable=False) #Should be either "owner" or "instrument"
    reviewComment = db.Column(db.String(400), nullable=False)

    @hybrid_property
    def ref_id(self):
        return self.ref_id_owner or self.ref_id_instrument

    def __init__(self, ref_id_owner, ref_id_instrument, ref_type, reviewComment):
        self.ref_id_owner = ref_id_owner
        self.ref_id_instrument = ref_id_instrument
        self.ref_type = ref_type
        self.reviewComment = reviewComment

    def json(self):
        return {"id":self.id, "ref_id":self.ref_id, "ref_type":self.ref_type, "reviewComment":self.reviewComment}


class RenterTransaction(db.Model):
    __tablename__ = "rentertransaction"
    id = db.Column(db.Integer, primary_key=True)
    totalPrice = db.Column(db.Float(2), nullable=False)
    fromDate = db.Column(db.Date, nullable=False)
    toDate = db.Column(db.Date, nullable=False)
    approvedStatus = db.Column(db.Boolean, nullable=False) #Maybe change to Enum
    isPaid = db.Column(db.Boolean, nullable=False)

    #Connection to Instrument Renter Details
    ins_renter_details_id = db.Column(db.Integer, db.ForeignKey('instrumentrenterdetails.id'))
    renter = db.relationship("InstrumentRenterDetails", back_populates='transactions')

    def __init__(self, ins_renter_details_id, totalPrice, fromDate, toDate, approvedStatus, isPaid):
        self.ins_renter_details_id = ins_renter_details_id
        self.totalPrice = totalPrice
        self.fromDate = fromDate
        self.toDate = toDate
        self.approvedStatus = approvedStatus
        self.isPaid = isPaid

    def json(self):
        return {"id":self.id, "ins_renter_details_id":self.ins_renter_details_id, "totalPrice":self.totalPrice, "fromDate":str(self.fromDate), "toDate":str(self.toDate), "approvedStatus":self.approvedStatus}


class RentedItem(db.Model):
    __tablename__ = "renteditem"
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Boolean, nullable=False) #If false, then the instrument has been returned and this is just a history of that item.

    #Connection to renter transaction
    renterTransactionID = db.Column(db.Integer, db.ForeignKey("rentertransaction.id"))
    renterTransaction = db.relationship("RenterTransaction")

    #Connection to instrument
    instrumentID = db.Column(db.Integer, db.ForeignKey("instrumentdetails.id"))
    instrument = db.relationship("Instrument")

    def __init__(self, renterTransactionID, instrumentID, status):
        self.renterTransactionID = renterTransactionID
        self.instrumentID = instrumentID
        self.status = status

    def json(self):
        return {"id":self.id, "renterTransactionID":self.renterTransactionID, "instrumentID":self.instrumentID, "status":self.status}
    
class Coupon(db.Model):
    __tablename__ = "coupon"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    percentDiscount = db.Column(db.Float(2), nullable=False) #Example: 10% discount would be stored as 0.1
    endDate = db.Column(db.Date, nullable=False)

    def __init__(self, name, percentDiscount, endDate):
        self.name = name
        self.percentDiscount = percentDiscount
        self.endDate = endDate

    def json(self):
        return {"id":self.id, "name":self.name, "percentDiscount":self.percentDiscount, "endDate":self.endDate}