import csv
from datetime import datetime

data = [
    ["name", "email", "type", "status", "last_sent"],
    ["Prasheetha s", "prasheethasenthilkumar22@gmail.com", "student", "Pending", ""],
    ["Ajay", "ajaiks2005@gmail.com", "alumni", "joined", ""],
    ["Prashee", "prasheetha212@gmail.com", "staff", "joined", ""],
    ["Monisha", "monishabala2005@gmail.com", "student", "Pending", ""],
    ["Rhooba", "prasheethaprasheetha212@gmail.com", "student", "pending", ""],
    ["Kanya", "kanyasaminathan@gmail.com", "student", "pending", ""],
    ["Riyas", "krriyas2003@gmail.com", "alumni", "joined", ""],
    ["vishwanathan", "vishwanathamrish@gmail.com", "staff", "joined", ""],


    
]

with open('contacts.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerows(data)
