from dbmodels import Rating, InstrumentImageDocs, db


#Helper function to get the average rating of an instrument.
def get_instrument_average_rating(instrumentID):
    total = 0
    numOfRatings = 0
    ratings = db.session.query(Rating).filter(Rating.ref_id_instrument == instrumentID, Rating.ref_type=="instrument").all()
    for row in ratings:
        total += row.rating
        numOfRatings += 1

    average = round(total/numOfRatings, 2) if numOfRatings != 0 else 0
    return average

#Helper function to get the images/media of an instrument.
def get_instrument_media(instrumentID):
    query = db.session.query(InstrumentImageDocs).filter(InstrumentImageDocs.instrumentID == instrumentID).all()
    mediaList = []

    for media in query:
        #mediaLinkSplit = media.mediaLink.split("/")
        #jsonMedia = media.json()
        #newLink = "http://drive.google.com/uc?export=view&id=" + str(mediaLinkSplit[5])
        #jsonMedia['mediaLink'] = newLink
        mediaList.append(media.json())

    return mediaList