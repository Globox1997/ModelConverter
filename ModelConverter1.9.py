# -*- coding: utf-8 -*-
"""
Created on Tue Jun 15 11:27:58 2021

@author: Globox_Z

Class has to have constructor with empty ()
"""

# All library stuff
import tkinter as tk
from tkinter.filedialog import askopenfilename
import re
from tkinter import * 
from tkinter.ttk import *
import os

root = tk.Tk() #Mandatory for Window
root.geometry('300x100') #Window Size
root.title("Model Converter") #Window Title

def open_file():
    path = askopenfilename(title="Select File")

    if path == "":
        root.destroy()
        return
    file = open(path)
    
    fileLineEdit = file.readlines()
    fileLineEdit.insert(0,"// Made with Model Converter by Globox_Z\n")
    fileLineEdit.insert(1,"// Generate all required imports\n")
    
    
    lineIndex = 0
    partTicker = 0
    textureSize = 0
    childTicker = 0
    childFromChildTicker = 0
    
    # look for texture - square only
    for texture in fileLineEdit:
        if "setTextureSize" in texture:
            textureSize= int(re.search(r'\d+', texture).group())
            break
        else:
            # check for blockbenchlike texture size
            if "textureWidth" in texture:
                textureSize= int(re.search(r'\d+', texture).group())
                fileLineEdit[fileLineEdit.index(texture)+1] = ""
                fileLineEdit[fileLineEdit.index(texture)] = ""
                break
    
    
    javaFileName = str(os.path.basename(path).replace(".java", "()"))
    # add 1.17 methods
    for line in fileLineEdit:
        if javaFileName in line:    
            lineIndex = index = fileLineEdit.index(line)
            fileLineEdit[index] = fileLineEdit[index].replace("Model()", "Model(ModelPart root)")
            fileLineEdit.insert(index+1, "}\n")
            fileLineEdit.insert(index+2, "public static TexturedModelData getTexturedModelData() {\n")
            fileLineEdit.insert(index+3, "ModelData modelData = new ModelData();\n")
            fileLineEdit.insert(index+4, "ModelPartData modelPartData = modelData.getRoot();\n")
            break

    # check for ModelParts and add them to new model method
    for anotherLine in fileLineEdit:
        if "final ModelPart" in anotherLine:
            partTicker +=1
            anotherLine = anotherLine.split(" ")
            insertLine = anotherLine[-1]
            insertLine = insertLine.replace(";\n",' = root.getChild("'+insertLine.replace(';\n','"'))
            insertLine = "this."+insertLine+");\n"
            fileLineEdit.insert(lineIndex+partTicker,insertLine)
    
    childTicker = lineIndex+partTicker
    # delete new ModePart lines
    for deleteLine in fileLineEdit:
        if "new ModelPart(this" in deleteLine:
            fileLineEdit[fileLineEdit.index(deleteLine)] = ""
        else:
            if "(new ModelPart(this))" in deleteLine:
                fileLineEdit[fileLineEdit.index(deleteLine)] = ""

    # edit all pivot part lines
    for pivotLine in fileLineEdit:
        pivot = []
        if ".setPivot" in pivotLine:
            # lineAdder set for this. lines
            lineAdder = 1
            if "this." in pivotLine:
                lineAdder = 0
            # Get pivot
            newPivotLine = pivotLine.split(".",2-lineAdder)
            pivot = re.findall(r"[-+]?\d*\.\d+|\d+", newPivotLine[2-lineAdder])
            
            fileLineEdit[fileLineEdit.index(pivotLine)] = ""
            addedCuboids = False
            # Get modelparts from given pivot part
            for lastLine in fileLineEdit:
                exactString = str(newPivotLine[1-lineAdder])+"."
                if exactString in lastLine:
                    if ".addCuboid" in lastLine:
                        newLastLine = lastLine.split(".",3-lineAdder)
                        if not "this." in lastLine:
                            newLastLine[1-lineAdder] = newLastLine[1-lineAdder].replace(" ", "")
                            newLastLine[1-lineAdder] = newLastLine[1-lineAdder].replace("\t", "")
                        newString = 'modelPartData.addChild("'+str(newLastLine[1-lineAdder])+'", ModelPartBuilder.create().uv'
                        cuboidSearch = str(newLastLine[1-lineAdder])+".setTextureOffset"
                        addedCuboids = True
                        for lastLineCuboid in fileLineEdit:
                            if cuboidSearch in lastLineCuboid:
                                newCuboidLine = lastLineCuboid.split(".",3-lineAdder)
                                uvList = re.findall(r'\d+', newCuboidLine[2-lineAdder])
                                cuboidString = newCuboidLine[3-lineAdder].replace("addCuboid", "cuboid")
                                
                                if ", 0.0F, false);\n" in cuboidString:
                                    cuboidString = cuboidString.replace(", 0.0F, false);\n",").uv")
                                else:
                                    cuboidString = cuboidString.replace(", 0.0F);\n",").uv")
                    
                                newString = newString+"("+str(uvList[0])+","+str(uvList[1])+")."+cuboidString
                                fileLineEdit[fileLineEdit.index(lastLineCuboid)] = ""
                        
                        pivotString = " ModelTransform.pivot("+str(pivot[0])+"F,"+str(pivot[1])+"F,"+str(pivot[2])+"F));\n"
                        newString = newString + pivotString
                        # remove .uv at the end of the line
                        newString = newString.replace(".uv ",", ")
                        
                        fileLineEdit.insert(lineIndex+childTicker, newString)
                        childTicker +=1
            # Get modelparts which don't have cuboids but have childs
            if not addedCuboids:
                # Check for "this." string
                if not "this." in lastLine:
                    newPivotLine[1-lineAdder] = newPivotLine[1-lineAdder].replace(" ", "")
                    newPivotLine[1-lineAdder] = newPivotLine[1-lineAdder].replace("\t", "")
                    
                newString = 'modelPartData.addChild("'+str(newPivotLine[1-lineAdder])+'", ModelPartBuilder.create(), ModelTransform.pivot('+str(pivot[0])+"F,"+str(pivot[1])+"F,"+str(pivot[2])+"F));\n"
                fileLineEdit.insert(lineIndex+childTicker, newString)   
                childTicker+=1
                # check for childTicker if its appropiate position for this extra line

            
    returnString = "return TexturedModelData.of(modelData,"+ str(textureSize)+","+str(textureSize)+");\n"
    fileLineEdit.insert(lineIndex+childTicker, returnString)

    # try:
    for checkForChilds in fileLineEdit:
        if ".addChild(" in checkForChilds:
            if not "modelPartData" in checkForChilds:
                childSplit = checkForChilds.split(".")
                
                # result = modelpart name
                result = re.search(r"\(([A-Za-z0-9_]+)\)", childSplit[2-lineAdder])
                result = result[0]
                result = result[:-1]
                result = result[1:]

                # Root change
                splitterString = "this."+ result+' = root.getChild("'+result+'");\n'

                if lineAdder == 1:
                    childSplit[1-lineAdder] = childSplit[1-lineAdder].replace(" ", "")
                    childSplit[1-lineAdder] = childSplit[1-lineAdder].replace("\t", "")

                splitterGetterString = "this."+ childSplit[1-lineAdder]+' = root.getChild("'+childSplit[1-lineAdder]+'");\n'

                # Erase root line
                fileLineEdit[fileLineEdit.index(splitterString)] = ""
                
                # Check for "this." string
                if  splitterGetterString not in fileLineEdit:
                    for extraChild in fileLineEdit:
                        extraChildString = "this."+childSplit[1-lineAdder]
                        if extraChildString in extraChild:
                            splitterGetterString = extraChild
                            break
                        
                fileLineEdit.insert(fileLineEdit.index(splitterGetterString)+1,"this."+ result +' = this.'+childSplit[1-lineAdder]+'.getChild("'+result+'");\n')
                
                # Erase .addChild line which still existed
                fileLineEdit[fileLineEdit.index(checkForChilds)] = ""
                
                
                # result is everything which adds childs
                # childSplit[1-lineAdder] is the father
                
                # Cuboid change
                
                for childHood in fileLineEdit:
                    notChild = 'modelPartData'
                    notOtherChild = '.addChild("'+str(childSplit[1-lineAdder])+'"'

                    if notChild in childHood:
                        if notOtherChild in childHood:
                            hooder = "= "+str(notChild)
                            if not hooder in childHood:
                                childFromChildTicker+=1
                                # Set father number
                                hoodSplitter =  "ModelPartData modelPartData"+str(childFromChildTicker)+" = "+childHood
                                fileLineEdit[fileLineEdit.index(childHood)] = hoodSplitter 

                            # Set right modelPart father number
                            for lastButNotLeast in fileLineEdit:
                                resultChecker = 'modelPartData'
                                resultOtherChecker = '.addChild("'+str(result)+'"'
                                if resultChecker in lastButNotLeast:
                                    if resultOtherChecker in lastButNotLeast:
                                        
                                        # Set for sure right father number
                                        for searchFather in fileLineEdit:
                                            fatherString = '.addChild("'+str(childSplit[1-lineAdder])+'"'
                                            if fatherString in searchFather:
                                                childOfChildOfChildNumber = int(re.search(r'\d+', searchFather).group())

                                        endLastButNotLeast = lastButNotLeast.replace("modelPartData.","modelPartData"+str(childOfChildOfChildNumber)+".")
                                        fileLineEdit[fileLineEdit.index(lastButNotLeast)] = endLastButNotLeast

                                
                                
    # Filter empty elements
    fileLineEdit = list(filter(lambda item: item != "\n", fileLineEdit))
    
    newfile = open(path.replace(".java","")+"CovertedModel.java", "w")
    newfile.writelines(fileLineEdit)
    newfile.close()

    root.destroy()
    
btn = Button(root, text ='Select File', command = lambda:open_file())#Button 
btn.grid(row=1, column=1) #Button Position
btn.place(relx=0.5, rely=0.5, anchor=CENTER)
mainloop() #Mandatory for window