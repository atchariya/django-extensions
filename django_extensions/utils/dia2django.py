# -*- coding: UTF-8 -*-
##Author Igor Támara igor@tamarapatino.org
##Use this little program as you wish, if you
#include it in your work, let others know you
#are using it preserving this note, you have
#the right to make derivative works, Use it
#at your own risk.
#Tested to work on(etch testing 13-08-2007):
#  Python 2.4.4 (#2, Jul 17 2007, 11:56:54)
#  [GCC 4.1.3 20070629 (prerelease) (Debian 4.1.2-13)] on linux2

import codecs
import gzip
import re
import sys
from pprint import pprint
import xml.etree.ElementTree as ET
from xml.dom.minidom import *  # NOQA

import six

dependclasses = ["User", "Group", "Permission", "Message"]

#Type dictionary translation types SQL -> Django
tsd = {
    "text": "TextField",
    "date": "DateField",
    "varchar": "CharField",
    "int": "IntegerField",
    "float": "FloatField",
    "serial": "AutoField",
    "boolean": "BooleanField",
    "numeric": "FloatField",
    "timestamp": "DateTimeField",
    "bigint": "IntegerField",
    "datetime": "DateTimeField",
    "date": "DateField",
    "time": "TimeField",
    "bool": "BooleanField",
    "int": "IntegerField",
}

#convert varchar -> CharField
v2c = re.compile('varchar\((\d+)\)')


def index(fks, id):
    """Looks for the id on fks, fks is an array of arrays, each array has on [1]
    the id of the class in a dia diagram.  When not present returns None, else
    it returns the position of the class with id on fks"""
    for i, j in fks.items():
        if fks[i][1] == id:
            return i
    return None


def addparentstofks(rels, fks):
    """Gets a list of relations, between parents and sons and a dict of
    clases named in dia, and modifies the fks to add the parent as fk to get
    order on the output of classes and replaces the base class of the son, to
    put the class parent name.
    """
    for j in rels:
        son = index(fks, j[1])
        parent = index(fks, j[0])
        fks[son][2] = fks[son][2].replace("models.Model", parent)
        if parent not in fks[son][0]:
            fks[son][0].append(parent)



def addassoctofks(rels, fks):
    """Gets a list of relations, between parents and sons and a dict of
    clases named in dia, and modifies the fks to add the parent as fk to get
    order on the output of classes and replaces the base class of the son, to
    put the class parent name.
    """
    # pprint(fks)
    for j in rels:
        parent = index(fks, j[1])
        dep_name = index(fks, j[0])

        relation = dep_name.lower() + " = models.ForeignKey(" + dep_name + ")\n    relation"
        fks[parent][2] = fks[parent][2].replace("relation", relation)
        # if parent not in fks[son][0]:
        #     fks[son][0].append(parent)

def cleanupoutput(clases):
    for j in clases:
        clases[j][2] = clases[j][2].replace("    relation\n", "")

def dia2file(archivo):
    f = codecs.open(archivo, "rb")
    #dia files are gzipped
    data = gzip.GzipFile(fileobj=f).read()
    return data

def dia2django(archivo):
    models_txt = ''
    f = codecs.open(archivo, "rb")
    #dia files are gzipped
    data = gzip.GzipFile(fileobj=f).read()
    ppal = parseString(data)
    #diagram -> layer -> object -> UML - Class -> name, (attribs : composite -> name,type)
    datos = ppal.getElementsByTagName("dia:diagram")[0].getElementsByTagName("dia:layer")[0].getElementsByTagName("dia:object")
    clases = {}
    herit = []
    assoc = []
    imports = six.u("")
    for i in datos:
        #Look for the classes
        if i.getAttribute("type") == "UML - Class":
            myid = i.getAttribute("id")

            for j in i.childNodes:
                if j.nodeType == Node.ELEMENT_NODE and j.hasAttributes():
                    first_field = ""


                    if j.getAttribute("name") == "name":
                        actclas = j.getElementsByTagName("dia:string")[0].childNodes[0].data[1:-1]
                        myname = "\nclass %s(models.Model) :\n" % actclas
                        clases[actclas] = [[], myid, myname, 0, ""]
                        # print "m2: " + mycomment

                    if j.getAttribute("name") == "comment":
                        mycomment = j.getElementsByTagName("dia:string")[0].childNodes[0].data[5:-1]
                        if len(mycomment) > 0:
                            clases[actclas][4] = "unicode(" + mycomment + ") or u''"

                    if j.getAttribute("name") == "attributes":
                        for l in j.getElementsByTagName("dia:composite"):
                            if l.getAttribute("type") == "umlattribute":
                                #Look for the attribute name and type
                                comment = ""
                                for k in l.getElementsByTagName("dia:attribute"):
                                    if k.getAttribute("name") == "name":
                                        nc = k.getElementsByTagName("dia:string")[0].childNodes[0].data[1:-1]

                                    elif k.getAttribute("name") == "comment":
                                        list = k.getElementsByTagName("dia:string")[0].childNodes[0].data[1:-1]
                                        if val == '##':
                                            val = ''
                                        else:
                                            list = list.split("\n")
                                            if list[0].startswith("#"):
                                                comment = list[0]
                                                del list[0]
                                            val = ', '.join(map(str,list))

                                    elif k.getAttribute("name") == "type":
                                        tc = k.getElementsByTagName("dia:string")[0].childNodes[0].data[1:-1]

                                        if tc.lower().startswith("fk") or tc.lower().startswith("mm"):
                                            relation_name = tc[3:-1]
                                            # if dependclasses.count(relation_name) == 0:
                                                    # dependclasses.append(relation_name)
                                            continue

                                    elif k.getAttribute("name") == "value":
                                        val = k.getElementsByTagName("dia:string")[0].childNodes[0].data[1:-1]
                                        if val == '##':
                                            val = ''
                                    elif k.getAttribute("name") == "visibility" and k.getElementsByTagName("dia:enum")[0].getAttribute("val") == "2":

                                        if tc.replace(" ", "").lower().startswith("manytomanyfield("):
                                                #If we find a class not in our model that is marked as being to another model
                                                newc = tc.replace(" ", "")[16:-1]
                                                if dependclasses.count(newc) == 0:
                                                        dependclasses.append(newc)
                                        if tc.replace(" ", "").lower().startswith("foreignkey("):
                                                #If we find a class not in our model that is marked as being to another model
                                                newc = tc.replace(" ", "")[11:-1]
                                                if dependclasses.count(newc) == 0:
                                                        dependclasses.append(newc)


                                #Mapping SQL types to Django
                                varch = v2c.search(tc)
                                if tc.replace(" ", "").startswith("ManyToManyField("):
                                    myfor = tc.replace(" ", "")[16:-1]
                                    if actclas == myfor:
                                        #In case of a recursive type, we use 'self'
                                        tc = tc.replace(myfor, "'self'")
                                    elif clases[actclas][0].count(myfor) == 0:
                                        #Adding related class
                                        if myfor not in dependclasses:
                                            #In case we are using Auth classes or external via protected dia visibility
                                            clases[actclas][0].append(myfor)
                                    tc = "models." + tc
                                    if len(val) > 0:
                                        tc = tc.replace(")", "," + val + ")")
                                elif tc.find("Field") != -1:
                                    if tc.count("()") > 0 and len(val) > 0:
                                        tc = "models.%s" % tc.replace(")", "," + val + ")")
                                    else:
                                        tc = "models.%s(%s)" % (tc, val)
                                elif tc.replace(" ", "").startswith("ForeignKey("):
                                    myfor = tc.replace(" ", "")[11:-1]
                                    if actclas == myfor:
                                        #In case of a recursive type, we use 'self'
                                        tc = tc.replace(myfor, "'self'")
                                    elif clases[actclas][0].count(myfor) == 0:
                                        #Adding foreign classes
                                        if myfor not in dependclasses:
                                            #In case we are using Auth classes
                                            clases[actclas][0].append(myfor)
                                    tc = "models." + tc
                                    if len(val) > 0:
                                        tc = tc.replace(")", "," + val + ")")
                                elif varch is None:
                                    if tc.lower().startswith("fk"):
                                        tc = "models.ForeignKey" + "(" + relation_name + ")"
                                        #Adding foreign classes
                                        if relation_name not in dependclasses:
                                            #In case we are using Auth classes
                                            clases[actclas][0].append(relation_name)
                                    elif tc.lower().startswith("mm"):
                                        tc = "models.ManyToManyField" + "(" + relation_name + ")"
                                        if relation_name not in dependclasses:
                                            #In case we are using Auth classes
                                            clases[actclas][0].append(relation_name)
                                    else:
                                        tc = "models." + tsd[tc.strip().lower()] + "(" + val + ")"
                                else:
                                    tc = "models.CharField(max_length=" + varch.group(1) + ")"
                                    if len(val) > 0:
                                        tc = tc.replace(")", ", " + val + ")")

                                if len(comment) > 0:
                                    tc = tc + " " + comment

                                if not (nc == "id" and tc == "AutoField()"):
                                    clases[actclas][2] = clases[actclas][2] + ("    %s = %s\n" % (nc, tc))
                                    if len(first_field) == 0:
                                        first_field = nc

                        if len(clases[actclas][4]) == 0:
                            clases[actclas][4] = "unicode(self." + first_field + ") or u''"

        elif i.getAttribute("type") == "UML - Generalization":
            mycons = ['A', 'A']
            a = i.getElementsByTagName("dia:connection")
            for j in a:
                if len(j.getAttribute("to")):
                    mycons[int(j.getAttribute("handle"))] = j.getAttribute("to")
            if 'A' not in mycons:
                herit.append(mycons)
        elif i.getAttribute("type") == "UML - SmallPackage":
            a = i.getElementsByTagName("dia:string")
            for j in a:
                if len(j.childNodes[0].data[1:-1]):
                    imports += six.u("from %s.models import *" % j.childNodes[0].data[1:-1])
        elif i.getAttribute("type") == "UML - Association":
            mycons = ['A', 'A']
            related_name = ''
            for k in i.getElementsByTagName("dia:attribute"):
                if k.getAttribute("name") == "name":
                    relation_name = k.getElementsByTagName("dia:string")[0].childNodes[0].data[1:-1]

            a = i.getElementsByTagName("dia:connection")
            for j in a:
                if len(j.getAttribute("to")):
                    mycons[int(j.getAttribute("handle"))] = j.getAttribute("to")

            if 'A' not in mycons:
                assoc.append(mycons)

    addparentstofks(herit, clases)
    # addassoctofks(assoc, clases)

    # print "My class"
    # pprint(clases)
    # cleanupoutput(clases)

    #Ordering the appearance of classes
    #First we make a list of the classes each classs is related to.
    ordered = []
    # pprint(dependclasses)
    for j, k in six.iteritems(clases):
        if len(k[4]) > 5 :
            k[2] = k[2] + "\n    def %s(self):\n        return %s\n" % (("__str__" if six.PY3 else "__unicode__"), k[4] ,)
        else:
            k[2] = k[2] + "\n    def %s(self):\n        return u\"\"\n" % (("__str__" if six.PY3 else "__unicode__"), )

        for fk in k[0]:
            if fk not in dependclasses:
                clases[fk][3] += 1
        ordered.append([j] + k)
    # pprint(ordered)
    i = 0
    while i < len(ordered):
        mark = i
        j = i + 1
        while j < len(ordered):
            if ordered[i][0] in ordered[j][1]:
                mark = j
            j += 1
        if mark == i:
            i += 1
        else:
            # swap %s in %s" % ( ordered[i] , ordered[mark]) to make ordered[i] to be at the end
            if ordered[i][0] in ordered[mark][1] and ordered[mark][0] in ordered[i][1]:
                #Resolving simplistic circular ForeignKeys
                print("Not able to resolve circular ForeignKeys between %s and %s" % (ordered[i][1], ordered[mark][0]))
                break
            a = ordered[i]
            ordered[i] = ordered[mark]
            ordered[mark] = a
        if i == len(ordered) - 1:
            break
    ordered.reverse()
    if imports:
        models_txt = str(imports)
    for i in ordered:
        models_txt += '%s\n' % str(i[3])

    return models_txt

if __name__ == '__main__':
    if len(sys.argv) == 2:
        print dia2django(sys.argv[1])
    else:
        print(" Use:\n \n   " + sys.argv[0] + " diagram.dia\n\n")
