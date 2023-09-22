# -*- coding: utf-8 -*-

import htbulma as b
from htag import Tag
import math,os,json,sys

# the folder, where app/apk can save data (parent folder)
FOLDER=os.path.join( os.path.dirname(os.path.abspath(os.path.realpath(sys.argv[0]))), ".." )

#############################################################################
## DB Part
#############################################################################

from tinydb import TinyDB,Query
from tinydb.storages import MemoryStorage
from datetime import datetime
from dataclasses import dataclass,asdict

class TinyTable:
    id=None
    db=None
    def delete(self):
        if self.id and self.db:
            self.db.remove( doc_ids=[self.id] )

    def update(self):
        if self.id and self.db:
            self.db.update( asdict(self), doc_ids=[self.id] )

def cast(db,id,klass,dico):
    doc= klass(**dico)
    doc.id = id
    doc.db = db
    return doc


@dataclass
class Payer(TinyTable):
    name: str
    color: str
    part: int = 1
    _type: str = "payer"

    def add_expense(self,price,title,date=None):
        if self.id and self.db:
            dico= asdict( Expense(payer_id=self.id, price=price, title=title, timestamp=date and date.timestamp() or datetime.now().timestamp()) )
            return cast(self.db, self.db.insert( dico ), Expense, dico )

    def expenses(self):
        if self.id and self.db:
            ll=[cast(self.db, i.doc_id, Expense, i) for i in self.db.search(Query().payer_id == self.id)]
            ll.sort(key=lambda i: -i.timestamp)
            return ll


@dataclass
class Expense(TinyTable):
    payer_id: int
    price: float
    title: str
    timestamp: float
    _type: str = "expense"

    @property
    def date(self):
        return datetime.fromtimestamp(self.timestamp)

    @property
    def payer(self):
        if self.db:
            dico = self.db.get(doc_id = self.payer_id)
            if dico:
                return cast(self.db, self.payer_id, Payer, dico)


class DB:
    def __init__(self,file=None):
        self.file=file
        if file is None:
            self._db = TinyDB(storage=MemoryStorage)
            self.name ="In-Memory"
        else:
            self._db = TinyDB(file)
            self.name =os.path.basename(file)[:-5].replace("_"," ")

    def create_payer(self,name:str,color:str="#EEEEFF"):
        p = Payer(name=name,color=color)
        p.id = self._db.insert( asdict(p) )
        p.db = self._db
        return p

    def payers(self):
        return [cast(self._db, i.doc_id, Payer, i) for i in self._db.search(Query()._type == Payer._type)]

    def expenses(self):
        ll=[cast(self._db, i.doc_id, Expense, i) for i in self._db.search(Query()._type == Expense._type)]
        ll.sort(key=lambda i: -i.timestamp)
        return ll

#~ #################
def test_db():
    d=DB()
    p1=d.create_payer("p1")
    p2=d.create_payer("p2")

    p1.name="p1 renamed"
    p1.update()

    p1.add_expense(12.50,"fdp")
    p2.add_expense(22.10,"2fdp")
    ex2=p2.add_expense(2.70,"2fdp")

    ex2.price=2.88
    ex2.update()

    for i in d.payers():
        print(i.id,i,i.expenses())
    for i in d.expenses():
        print(i.id,i,i.date,i.payer)
    p1.delete()
    ex2.delete()
    for i in d.payers():
        print(i.id,i,i.expenses())
    for i in d.expenses():
        print(i.id,i,i.date,i.payer)


#############################################################################
## Helpers Part
#############################################################################

def highcolor(color:str): #color : "#FF00FF"

    def isLightOrDark(rgbColor:str):
        r,g,b=int(rgbColor[0:2],16),int(rgbColor[2:4],16),int(rgbColor[4:6],16)
        hsp = math.sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b))
        if (hsp>127.5):
            return True
        else:
            return False

    return isLightOrDark(color[1:]) and "#000000" or "#FFFFFF"

class Conf(dict):
    def __init__(self,f):
        self._f = f
        try:
            with open(self._f,"r+") as fid:
                d=json.load( fid)
        except:
            d={}

        dict.__init__(self,d)

    def __setitem__(self,k,v):
        dict.__setitem__(self,k,v)
        self._save()
    def __delitem__(self,k):
        dict.__delitem__(self,k)
        self._save()

    def _save(self):
        with open(self._f,"w+") as fid:
            fid.write( json.dumps( dict(self), indent=4 ))

#############################################################################
## HTag Part
#############################################################################

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
class Fab(Tag.div):
    statics=r"""
.is-fab {
  position: fixed;
  right: 2rem;
  bottom: 2rem;
}
.is-circular { border-radius: 50%;padding:18px !important;font-size:20px}
    """

    def __init__(self,callback,icon="✚",**a):
        super().__init__(_class="is-fab")
        self <= Tag.span(_class="icon is-large") <= Tag.b(icon, _onclick=callback, _class="button is-circular is-info is-link")
#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\


class TagDate(Tag.span):
    def init(self,date,**a):
        self += date.strftime("%Y/%m/%d %H:%M")

class TagPrice(Tag.span):
    def init(self,price,**a):
        self["style"]="font-weight:900"
        self += f"{price:.2f}".replace(".",",")

class TagPayer(Tag.span):
    def init(self,payer: Payer,**a):
        self["class"]="tag"
        self["style"]="background:"+payer.color+";color: "+highcolor(payer.color);
        self += payer.name

class TagPart(Tag.span):
    def init(self,payer: Payer,cb,**a):
        self.item = payer
        self.value = payer.part
        self.cb=cb

    def render(self):
        self.clear()

        self += Tag.button("<",_onclick=lambda o: self.inc(-1), _class="button is-small",_disabled = self.value == 1,_title="Decrease parts")
        self += Tag.button(self.value, _class="button is-small", _disabled=True)
        self += Tag.button(">",_onclick=lambda o: self.inc(1), _class="button is-small",_title="Increase parts")

    def inc(self,v):
        self.value += v
        self.cb(self.item, self.value)



class ListExpenses(Tag.div):
    def init(self,db,cbedit,**a):
        totalSum=0

        ll=[]
        for expense in db.expenses():
            totalSum+=expense.price
            ll.append( ( Tag.div(Tag.a(expense.title,item=expense,_onclick=cbedit)) + TagDate(expense.date), TagPayer(expense.payer), TagPrice(expense.price)) )

        if totalSum>0:
            self += b.Box("Total: "+ TagPrice(totalSum) )
            self += b.Table(ll)
            self["style"].set("margin-bottom","90px")  # add empty space (so the FAB will never hide something)
        else:
            self += b.Box("No expenses yet ;-)" )



class ListPayers(Tag.div):
    def init(self,db,cbedit,cbdelete,cbcolor,cbpart,**a):
        for payer in db.payers():
            somme = sum([e.price for e in payer.expenses()])
            bcolor=Tag.div( b.Input(payer.color,item=payer, _type="color",_onchange=lambda o: cbcolor(o.item,o.value) ),  _style="flex: 0 0 60px !important", _title="Change color")
            if not somme:
                show = Tag.A("X",item=payer,_onclick=cbdelete,_class="is-danger",_title="Delete this Payer")
            else:
                show = TagPrice(somme,_title="Expenses incurred")

            bname = Tag.a(payer.name,item=payer, _onclick=cbedit, _title="Edit the Payer's Name")
            bpart=TagPart(payer, cbpart )

            self += b.Box( b.HBox(bcolor,bname,bpart,show) )


class FormExpense(Tag.div):
    def init(self,db,payer,payer_id,pay=None,title=None,date=None,cbvalid=None,cbdelete=None,**a):
        if not date: date = datetime.now()

        HDATE = "%Y-%m-%dT%H:%M"

        def submit(f):
            pay=float(f["pay"])
            title=f["title"]
            date=datetime.strptime(f["date"],HDATE)
            payer_id=int(f["groupid"])
            if pay>0 and cbvalid:
                cbvalid(pay, title, payer_id, date)

        ff=b.Fields()
        ff.addField( "Amount", b.Input(pay or "",name="pay",js="self.focus()",_type="number",_step=0.01,_required=True) )
        ff.addField( "Title", b.Input(title or "",name="title",_required=True) )
        ff.addField( "Date", b.Input(date.strftime(HDATE),_name="date",_type="datetime-local") )
        if payer:
            ff <= Tag.input(_value=payer_id,_name="groupid",_type="hidden")
            ff.addField( "From", TagPayer(payer) )
            ff.addField( "", Tag.input(_value="Add",_type="submit",_class="button is-info"))
        else:
            ff.addField( "From", b.Select(payer_id,{i.id:i.name for i in db.payers()},_name="groupid") )
            ff.addField( "", b.HBox( Tag.input(_value="Modify",_type="submit",_class="button is-info"), Tag.input(_value="Delete",_type="button",_class="button is-danger",_onclick=lambda o: cbdelete() ) ))
            self += b.Content( Tag.h1("Edit") )

        self <= b.Form(onsubmit=submit) <= ff

class Selector(Tag.div):
    def init(self,folder,cb,**a):
        self.folder=folder
        self.cb=cb
        self._mbox = b.MBox(self)
        self.main = b.Box()

        self <= b.Box(b.Content(Tag.h1("TriApp")))
        self <= self.main

        self.redraw()

    def redraw(self):
        ll=[]
        for i in sorted(os.listdir(self.folder)):
            if i.endswith(".json"):
                fullpath = os.path.realpath( os.path.join(self.folder,i) )
                ll.append( b.HBox(
                        b.Button( DB(fullpath).name, path=fullpath, _onclick = self.select ),
                        b.Button( "X", path=fullpath, _onclick = self.delete, _class="is-danger",_style="flex: 0 0 40px",_title="Delete account" ),
                    )
                )

        ll.append(b.Button("✚",_class="is-warning",_onclick=self.create,_title="Create a new account"))

        self.main.set( b.VBox(*ll) )

    def select(self,o): #o.path:str
        self.cb(o.path)

    def delete(self,o): #o.path:str
        def sure():
            print("DELETE",o.path)
            os.unlink( o.path)
            self.redraw()

        self._mbox.confirm(f"Really delete '{o.path}' ?", sure)

    def create(self,o):
        def valid(name):
            name=name.strip()
            name=name.replace(" ","_")
            name=name.replace("/","_")
            name=name.replace(":","_")
            if name:
                fullpath = os.path.realpath( os.path.join(self.folder,name)+".json" )
                self.cb(fullpath)

        self._mbox.prompt("New Account","",valid)

class Gear(Tag.span):
    def init(self,**a):
        self <= "&#9881;"
        self["style"]="color:white;cursor:pointer;font-size:2em;position:fixed;z-index:10000;top:2px;right:10px"


class App(Tag.body):

    def init(self):
        self.cfg=Conf( os.path.join(FOLDER,"triapp.conf") )

        self.title=Tag.span("TriApp")

        # get opent db filename
        fp=self.cfg.get("current",None)

        self.initialize(fp)

    def initialize(self,fullpath=None):
        self.clear()
        if not fullpath:
            self <= Selector( FOLDER, self.initialize )
        else:
            self.db = DB(fullpath)

            # save opent db filename
            self.cfg["current"] = fullpath

            if len(self.db.payers())==0:
                self.db.create_payer( "You" )

            self._mbox = b.MBox(self)

            ##-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
            #~ self.nav = b.Nav(self.title)
            #~ self.nav.addEntry("Expenses", self.page_expenses )
            #~ self.nav.addEntry("Payers", self.page_payers )
            #~ self.nav.addEntry("Close", self.close  )
            ##-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
            Entry = lambda n,cb: Tag.a(n, _onclick = lambda o: cb(),_style="padding:10px")
            menus=b.VBox(
                Entry("Expenses",self.page_expenses),
                Entry("Payers",self.page_payers),
                Entry("QUIT",self.exit),
            )
            self.nav= b.NavSide(self.title, menus, "100px")
            ##-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:

            self.main = Tag.div()

            # create the layout
            self += self.nav
            self += b.Content( self.main)
            self += Fab( self.fab_add )

            self.page_expenses()

    def select_trip(self,o):
        self.nav.hide()
        # clear opent db filename
        del self.cfg["current"]

        self.call.initialize()

    def page_expenses(self):
        self.nav.hide()
        self.mode = 1
        self.title.set( f'Expenses for "{self.db.name}"' )
        self.title <= Gear(_onclick=self.select_trip)
        self.redraw()

    def page_payers(self):
        self.nav.hide()
        self.mode = 2
        self.title.set( f'Payers for "{self.db.name}"' )
        self.title <= Gear(_onclick=self.select_trip)
        self.redraw()

    def redraw(self):
        if self.mode==1:
            self.main.set( ListExpenses( self.db, self.edit_payment ) )
        else:
            self.main.set( ListPayers( self.db, self.edit_payer, self.delete_payer, self.change_color, self.change_part ) )

            #---------------------------------------------------------------------
            totalSum=sum([expense.price for expense in self.db.expenses()])
            if totalSum>0:
                ll=[Tag.div("Out of the total : "+TagPrice(totalSum))]
                totalParts= sum([payer.part for payer in self.db.payers()])
                for payer in self.db.payers():
                    percent = (100/totalParts) * payer.part
                    partage = (totalSum/totalParts) * payer.part
                    somme = sum([expense.price for expense in payer.expenses()])
                    if somme:
                        txt= ", but has already paid "+ TagPrice(somme)
                    else:
                        txt=", paid nothing"

                    balance = partage - somme
                    if balance<0:
                        txt += " : he must therefore recover "+TagPrice( abs(balance) )
                    else:
                        txt += " : so he has to pay "+TagPrice( abs(balance) )
                    ll.append( Tag.div( TagPayer(payer) + " should "+TagPrice(partage)+f"({percent:.2f}%)" + txt ) )

                content=b.Box()
                content+=Tag.h1("How to close:")
                content+=ll


                self.main<=content
            #---------------------------------------------------------------------



    def fab_add(self,o):
        if self.mode==1:
            self.add_payment()
        else:
            self.add_payer()

    def edit_payment(self,o):   # o.item: Expense
        def update(price:float, title:str, payer_id:int, date:datetime ):
            o.item.price = price
            o.item.title = title
            o.item.timestamp = date.timestamp()
            o.item.payer_id = payer_id
            o.item.update()

            self._mbox.close()
            self.redraw()

        def delete():
            def sure():
                o.item.delete()
                self._mbox.close()
                self.redraw()

            self._mbox.confirm(f"Really delete '{o.item.title}' of "+TagPrice(o.item.price)+" ?", sure)

        self._mbox.show( FormExpense( self.db, None, o.item.payer_id, o.item.price, o.item.title, date=o.item.date, cbvalid=update, cbdelete=delete ) )

    def add_payment(self):

        def select(payer:Payer):
            def insert(price:float, title:str,payer_id:int, date:datetime ):

                payer.add_expense(price,title,date)

                self._mbox.close()
                self.redraw()

            self._mbox.show( FormExpense( self.db, payer, payer.id, cbvalid=insert ) )


        payers = self.db.payers()
        if len(payers)>1:
            content=Tag.div()
            content+=Tag.h1("Whose has paid ?")

            for payer in payers:
                g=TagPayer(payer,_onclick=lambda o: select(o.item))
                g.item = payer
                g["style"].set("cursor","pointer !important")
                g["style"].set("font-size","1.2em")
                g["style"].set("width","33%")
                content+=g

            self._mbox.show( b.Content(content) )
        else:
            select( payers[0] )

    def add_payer(self):

        def valid(name):
            name=name.strip()
            if name:
                self.db.create_payer(name)
                self.redraw()

        self._mbox.prompt("New Payer Name ?","",valid)



    def edit_payer(self,o): # o.item: Payer

        def valid(name):
            name=name.strip()
            if name:
                o.item.name = name
                o.item.update()
                self.redraw()

        self._mbox.prompt("Rename Payer:",o.item.name,valid)


    def delete_payer(self,o): # o.item: Payer
        o.item.delete()
        self.redraw()

    def change_color(self, payer:Payer, new_color:str):
        payer.color = new_color
        payer.update()
        self.redraw()

    def change_part(self, payer:Payer,new_part:int):
        payer.part = new_part
        payer.update()
        self.redraw()

if __name__=="__main__":
    from htag.runners import AndroidApp
    AndroidApp( App ).run()

#=================================================================================
# from htag.runners import DevApp as Runner
# app=Runner(App)
# if __name__=="__main__":
#     app.run()
