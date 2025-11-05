from pymongo import MongoClient

client = MongoClient('mongodb+srv://brijamandarshan:brijamandarshan323140@cluster0.yqzmy.mongodb.net/messbuddy')
db = client.messbuddy

for mess in db.messes.find().limit(3):
    print(f"Mess: {mess['Mess_Name']}")
    print(f"  Ratings type: {type(mess.get('Ratings', []))}, value: {mess.get('Ratings', [])}")
    print(f"  RatedBy type: {type(mess.get('RatedBy', []))}, value: {mess.get('RatedBy', [])}")
    if mess.get('Ratings'):
        print(f"  First rating type: {type(mess['Ratings'][0])}")
    if mess.get('RatedBy'):
        print(f"  First RatedBy type: {type(mess['RatedBy'][0])}")
    print()
