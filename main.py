from operator import index
from fastapi import FastAPI, Request
from config import settings
import pyodbc
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")


db_URL = (f"DRIVER={settings.db_driver};"
          f"Server={settings.db_server};"
          f"Database={settings.db_name};"
          f"UID={settings.db_user};"
          f"PWD={settings.db_password};"
          # "Trusted_Connection=yes;"
          )
#globalne listy jednoelementowe, na maxa z paczki, którą rozładowywują
max_first_ktl = []
max_first_pro = []


#generator bieżącej kolekcji torów w danym odczycie
def gen(lista):
    i = 0
    while i < len(lista):
        yield lista[i][7]
        i += 1


@app.get('/', tags=["GetFromView"], response_class=HTMLResponse)
def get_programs(request: Request):
   
    try:
        conn = pyodbc.connect(db_URL)
        query_ktl = """select * from dbo.PodajDaneProgramu('KTL')order by id asc,lp desc"""
        query_pro = """select * from dbo.PodajDaneProgramu('PRO')order by id asc,lp desc"""
        query_counters_list = """SELECT * FROM [dbo].[packdetail]"""
        cursor = conn.cursor()
        cursor.execute(query_ktl)
        buffor_ktl = cursor.fetchall()
        cursor.execute(query_pro)
        buffor_pro = cursor.fetchall()
        cursor.execute(query_counters_list)
        multiples = cursor.fetchall()                     
        conn.close()
        totalKTL = str(len(buffor_ktl))
        totalPRO = str(len(buffor_pro))
        print(f"totale: KTL{totalKTL} PRO{totalPRO}")
    except pyodbc.OperationalError:
        conn.close()
        return HTMLResponse("__Server MSSQL is not found or not accessible__")
    # znakowanie paczek przez batch 
    batch = 1
    
    for belka in buffor_ktl:

        idx = buffor_ktl.index(belka)
    
        if idx >=1:
            if buffor_ktl[idx][3] == buffor_ktl[idx-1][3] and buffor_ktl[idx][1] == buffor_ktl[idx-1][1]:
                batch = batch 
            else:
                batch = batch +1
        else:
            batch = 1

        buffor_ktl[buffor_ktl.index(belka)] = list(belka) + [batch]   
    # tworzenie listy oraz skrócenie wielokrotnego wystąpienia w liście do pojedynczego z licznikiem: ile występuje 
    buffor_ktl_cc = []
    
    for value in set(gen(buffor_ktl)):
        tmp = []
        counter = 0
        for element in buffor_ktl:
            if element[7] == value:
                counter += 1
                tmp.append(element)
        buffor_ktl_cc.append(tmp[-1] + [counter])
    # przeliczenie z mnożnikami z bazy itechowej
    for record in list(buffor_ktl_cc):
        nr = record[3]
        belek = int(record[8])
        
        for el in multiples:
            if el[1] == nr:
                ilosc_detali = belek * int(el[2])
                ilosc_pojemnikow = int((ilosc_detali / int(el[3])) + (ilosc_detali % int(el[3])>0))
                ilosc_zawieszek = belek * int(el[4])
                buffor_ktl_cc[buffor_ktl_cc.index(record)] = record + [(ilosc_detali, ilosc_pojemnikow, ilosc_zawieszek)]
    # usunięcie rekordów nieobsługiwanych w bazie itechowej - nie ma ich przeliczników dla tego konkretnego NrPRM
    for t in list(buffor_ktl_cc):
        if len(t) < 10:
            buffor_ktl_cc.remove(t)
  
#######################################################################################################################################
#######################################################################################################################################
#######################################################################################################################################
    # znakowanie paczek przez batch 
    batch = 1
    
    for belka in buffor_pro:

        idx = buffor_pro.index(belka)
    
        if idx >=1:
            if buffor_pro[idx][3] == buffor_pro[idx-1][3] and buffor_pro[idx][1] == buffor_pro[idx-1][1]:
                batch = batch 
            else:
                batch = batch +1
        else:
            batch = 1

        buffor_pro[buffor_pro.index(belka)] = list(belka) + [batch]   
    # tworzenie listy oraz skrócenie wielokrotnego wystąpienia w liście do pojedynczego z licznikiem: ile występuje 
    buffor_pro_cc = []
    
    for value in set(gen(buffor_pro)):
        tmp = []
        counter = 0
        for element in buffor_pro:
            if element[7] == value:
                counter += 1
                tmp.append(element)
        buffor_pro_cc.append(tmp[-1] + [counter])
    # przeliczenie z mnożnikami z bazy itechowej
    for record in list(buffor_pro_cc):
        nr = record[3]
        belek = int(record[8])
        
        for el in multiples:
            if el[1] == nr:
                ilosc_detali = belek * int(el[2])
                ilosc_pojemnikow = int((ilosc_detali / int(el[3])) + (ilosc_detali % int(el[3])>0))
                ilosc_zawieszek = belek * int(el[4])
                buffor_pro_cc[buffor_pro_cc.index(record)] = record + [(ilosc_detali, ilosc_pojemnikow, ilosc_zawieszek)]
    # usunięcie rekordów nieobsługiwanych w bazie itechowej - nie ma ich przeliczników dla tego konkretnego NrPRM
    for t in list(buffor_pro_cc):
        if len(t) < 10:
            buffor_pro_cc.remove(t)
   # insert do listy globalnej i pretrzymanie największej wartości paczki
   # dla KTL
    if len(buffor_ktl_cc) >= 1:
        if len(max_first_ktl) < 1:
            max_first_ktl.append(buffor_ktl_cc[0])

        elif len(max_first_ktl) == 1 and max_first_ktl[0][3] == buffor_ktl_cc[0][3]:
            if max_first_ktl[0][9][0] < buffor_ktl_cc[0][9][0]:
                max_first_ktl[0] = buffor_ktl_cc[0]

        elif len(max_first_ktl) == 1 and max_first_ktl[0][3] != buffor_ktl_cc[0][3]:
            max_first_ktl[0] = buffor_ktl_cc[0]
    else:
        print("Przypadek jak na linii [KTL] nie ma obsługiwanego pakietu.")
        max_first_ktl.clear()
        
    # dla PRO
    if len(buffor_pro_cc) >= 1:
        if len(max_first_pro) < 1:
            max_first_pro.append(buffor_pro_cc[0])

        elif len(max_first_pro) == 1 and max_first_pro[0][3] == buffor_pro_cc[0][3]:
            if max_first_pro[0][9][0] < buffor_pro_cc[0][9][0]:
                max_first_pro[0] = buffor_pro_cc[0]
                
        elif len(max_first_pro) == 1 and max_first_pro[0][3] != buffor_pro_cc[0][3]:
            max_first_pro[0] = buffor_pro_cc[0]
    else:
        print("Przypadek jak na linii [PRO] nie ma obsługiwanego pakietu.")
        max_first_pro.clear()
        

    # wystawienie maxów jako zmienne
    try:
        max_ktl = max_first_ktl[0][9][0]
    except IndexError:
        max_ktl = 0
    
    try:
        max_pro = max_first_pro[0][9][0]
    except IndexError:
        max_pro = 0
                
    #Printy na konsole do śledzenia serwisu:
    print("\n----------------------------------RAW FROM DB------------------------------------")
    # Wyświetlenie tabel - bo mogę ;)
    print("RAW KTL")
    for raw_ktl in buffor_ktl:
        print(f'{buffor_ktl.index(raw_ktl)}--({raw_ktl[3]})--{raw_ktl}')
    print("\nRAW PRO")
    for raw_pro in buffor_pro:
        print(f'{buffor_pro.index(raw_pro)}--({raw_pro[3]})--{raw_pro}')
    print("\n- - - - - - - - - - - - - - - - - -ON PAGE - - - - - - - - - - - - - - - - - - - -")
    print("PREPARED KTL")
    for after_ktl in buffor_ktl_cc:
        print(f'{buffor_ktl_cc.index(after_ktl)}--({after_ktl[3]})--(x{after_ktl[8]})--{after_ktl}')
    print("\nPREPARED PRO")
    for after_pro in buffor_pro_cc:
        print(f'{buffor_pro_cc.index(after_pro)}--({after_pro[3]})--(x{after_pro[8]})--{after_pro}')
    
    print("\n-----------------------------------ANOTHER VALUES-----------------------------------")
    if len(buffor_ktl_cc) >= 1:
        print("-- FIRST ON KTL -- : Do rozładowania:", buffor_ktl_cc[0][9][0],"z", max_first_ktl[0][9][0], "detalu:", buffor_ktl_cc[0][4])
        print("len(ktl)", len(max_first_ktl))
    if len(buffor_pro_cc) >= 1:
        print("-- FIRST ON PRO -- : Do rozładowania:", buffor_pro_cc[0][9][0],"z", max_first_pro[0][9][0], "detalu:", buffor_pro_cc[0][4])
        print("len(pro)", len(max_first_pro))

    return templates.TemplateResponse("index.html", {"request": request, "buffor_ktl": buffor_ktl_cc, "buffor_pro": buffor_pro_cc,
                                     "totalKTL":totalKTL, "totalPRO":totalPRO, "max_ktl": max_ktl, "max_pro": max_pro})