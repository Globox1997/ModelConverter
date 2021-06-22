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
    
    file_line_edit = file.readlines()
    file_line_edit.insert(0,"// Made with Model Converter by Globox_Z\n")
    file_line_edit.insert(1,"// Generate all required imports\n")
    
    
    line_index = 0
    part_ticker = 0
    texture_size = 0
    child_ticker = 0
    child_from_child_ticker = 0
    
    # look for texture - square only
    for texture_string in file_line_edit:
        if "setTextureSize" in texture_string:
            texture_size= int(re.search(r'\d+', texture_string).group())
            break
        else:
            # check for blockbenchlike texture size
            if "textureWidth" in texture_string:
                texture_size= int(re.search(r'\d+', texture_string).group())
                file_line_edit[file_line_edit.index(texture_string)+1] = ""
                file_line_edit[file_line_edit.index(texture_string)] = ""
                break
    
    
    java_file_name = str(os.path.basename(path).replace(".java", "()"))
    # add 1.17 methods
    for line in file_line_edit:
        if java_file_name in line:
            line_index = index = file_line_edit.index(line)
            file_line_edit[index] = file_line_edit[index].replace("Model()", "Model(ModelPart root)")
            file_line_edit.insert(index+1, "}\n")
            file_line_edit.insert(index+2, "public static TexturedModelData getTexturedModelData() {\n")
            file_line_edit.insert(index+3, "ModelData modelData = new ModelData();\n")
            file_line_edit.insert(index+4, "ModelPartData modelPartData = modelData.getRoot();\n")
            break
    else:
        print("Couldn't find main method")
        tk.messagebox.showerror(title=None, message="Error: Main method not found!\nFile name has to be the same as the class name!\nOnly one constructor is allowed!\nConstructor has to have empty brackets!\n")
        root.destroy()
        return
    # check for ModelParts and add them to new model method
    for another_line in file_line_edit:
        if "final ModelPart" in another_line:
            part_ticker +=1
            another_line = another_line.split(" ")
            insert_line = another_line[-1]
            insert_line = insert_line.replace(";\n",' = root.getChild("'+insert_line.replace(';\n','"'))
            insert_line = "this."+insert_line+");\n"
            file_line_edit.insert(line_index+part_ticker,insert_line)

    child_ticker = line_index+part_ticker
    # delete new ModePart lines
    for delete_line in file_line_edit:
        if "new ModelPart(this" in delete_line:
            file_line_edit[file_line_edit.index(delete_line)] = ""
        else:
            if "(new ModelPart(this))" in delete_line:
                file_line_edit[file_line_edit.index(delete_line)] = ""

    # edit all pivot part lines
    for pivot_line in file_line_edit:
        pivot = []
        if ".setPivot" in pivot_line:
            # line_adder set for this. lines
            line_adder = 1
            if "this." in pivot_line:
                line_adder = 0
            # Get pivot
            new_pivot_line = pivot_line.split(".",2-line_adder)
            pivot = re.findall(r"[-+]?\d*\.\d+|\d+", new_pivot_line[2-line_adder])
            
            file_line_edit[file_line_edit.index(pivot_line)] = ""
            added_cuboids = False
            # Get modelparts from given pivot part
            for last_line in file_line_edit:
                exact_string = str(new_pivot_line[1-line_adder])+"."
                if exact_string in last_line:
                    if ".addCuboid" in last_line:
                        new_last_line = last_line.split(".",3-line_adder)
                        if not "this." in last_line:
                            new_last_line[1-line_adder] = new_last_line[1-line_adder].replace(" ", "")
                            new_last_line[1-line_adder] = new_last_line[1-line_adder].replace("\t", "")
                        new_string = 'modelPartData.addChild("'+str(new_last_line[1-line_adder])+'", ModelPartBuilder.create().uv'
                        cuboid_search_string = str(new_last_line[1-line_adder])+".setTextureOffset"
                        added_cuboids = True
                        for last_line_cuboid in file_line_edit:
                            if cuboid_search_string in last_line_cuboid:
                                new_cuboid_line = last_line_cuboid.split(".",3-line_adder)
                                uvList = re.findall(r'\d+', new_cuboid_line[2-line_adder])
                                cuboid_string = new_cuboid_line[3-line_adder].replace("addCuboid", "cuboid")
                                
                                if ", 0.0F, false);\n" in cuboid_string:
                                    cuboid_string = cuboid_string.replace(", 0.0F, false);\n",").uv")
                                elif ", 0.0F);\n" in cuboid_string:
                                    cuboid_string = cuboid_string.replace(", 0.0F);\n",").uv")
                                elif ", 0.0F, true);\n" in cuboid_string:
                                    cuboid_string = cuboid_string.replace(", 0.0F, true);\n",", true).uv")
                                elif ", false);\n" in cuboid_string:
                                    dilation = re.findall(r"[-+]?\d*\.\d+|\d+", cuboid_string)
                                    cuboid_string = cuboid_string.replace(", "+str(dilation[6])+"F, false);\n",", new Dilation("+str(dilation[6])+"F)).uv")
                                else:
                                    cuboid_string = cuboid_string.replace(");\n",").uv")
                                    if "true" in cuboid_string:
                                        error_string = last_line_cuboid.replace("\t","")
                                        print("Dilation and mirroring on one cube is not allowed here:\n"+str(error_string))
                                        tk.messagebox.showerror(title=None, message="Error: Dilation and mirroring on one cube is not allowed here:\n"+str(error_string))
                                        root.destroy()
                                        return
                    
                                new_string = new_string+"("+str(uvList[0])+","+str(uvList[1])+")."+cuboid_string
                                file_line_edit[file_line_edit.index(last_line_cuboid)] = ""
                        
                        pivot_string = " ModelTransform.pivot("+str(pivot[0])+"F,"+str(pivot[1])+"F,"+str(pivot[2])+"F));\n"
                        new_string = new_string + pivot_string
                        # remove .uv at the end of the line
                        new_string = new_string.replace(".uv ",", ")
                        
                        file_line_edit.insert(line_index+child_ticker, new_string)
                        child_ticker +=1
            # Get modelparts which don't have cuboids but have childs
            if not added_cuboids:
                # Check for "this." string
                if not "this." in last_line:
                    new_pivot_line[1-line_adder] = new_pivot_line[1-line_adder].replace(" ", "")
                    new_pivot_line[1-line_adder] = new_pivot_line[1-line_adder].replace("\t", "")
                    
                new_string = 'modelPartData.addChild("'+str(new_pivot_line[1-line_adder])+'", ModelPartBuilder.create(), ModelTransform.pivot('+str(pivot[0])+"F,"+str(pivot[1])+"F,"+str(pivot[2])+"F));\n"
                file_line_edit.insert(line_index+child_ticker, new_string)   
                child_ticker+=1
                # check for child_ticker if its appropiate position for this extra line

            
    return_string = "return TexturedModelData.of(modelData,"+ str(texture_size)+","+str(texture_size)+");\n"
    file_line_edit.insert(line_index+child_ticker, return_string)

    try:
        for check_for_childs in file_line_edit:
            if ".addChild(" in check_for_childs:
                if not "modelPartData" in check_for_childs:
                    child_string_split = check_for_childs.split(".")
                    
                    # result = modelpart name
                    result = re.search(r"\(([A-Za-z0-9_]+)\)", child_string_split[2-line_adder])
                    result = result[0]
                    result = result[:-1]
                    result = result[1:]
    
                    # Root change
                    root_change_string = "this."+ result+' = root.getChild("'+result+'");\n'
    
                    if line_adder == 1:
                        child_string_split[1-line_adder] = child_string_split[1-line_adder].replace(" ", "")
                        child_string_split[1-line_adder] = child_string_split[1-line_adder].replace("\t", "")
    
                    root_get_string = "this."+ child_string_split[1-line_adder]+' = root.getChild("'+child_string_split[1-line_adder]+'");\n'
    
                    # Erase root line
                    file_line_edit[file_line_edit.index(root_change_string)] = ""
                    
                    # Check for "this." string
                    if  root_get_string not in file_line_edit:
                        for extra_child in file_line_edit:
                            extra_child_string = "this."+child_string_split[1-line_adder]
                            if extra_child_string in extra_child:
                                root_get_string = extra_child
                                break
                            
                    file_line_edit.insert(file_line_edit.index(root_get_string)+1,"this."+ result +' = this.'+child_string_split[1-line_adder]+'.getChild("'+result+'");\n')
                    
                    # Erase .addChild line which still existed
                    file_line_edit[file_line_edit.index(check_for_childs)] = ""
                    
                    
                    # result is everything which adds childs
                    # child_string_split[1-line_adder] is the father
                    
                    # Cuboid change
                    
                    for child_cuboid in file_line_edit:
                        child_string_one = 'modelPartData'
                        child_string_two = '.addChild("'+str(child_string_split[1-line_adder])+'"'
    
                        if child_string_one in child_cuboid:
                            if child_string_two in child_cuboid:
                                exact_child_addition = "= "+str(child_string_one)
                                if not exact_child_addition in child_cuboid:
                                    child_from_child_ticker+=1
                                    # Set father number
                                    father_string =  "ModelPartData modelPartData"+str(child_from_child_ticker)+" = "+child_cuboid
                                    file_line_edit[file_line_edit.index(child_cuboid)] = father_string 
    
                                # Set right modelPart father number
                                for number_correction in file_line_edit:
                                    result_string_one = 'modelPartData'
                                    result_string_two = '.addChild("'+str(result)+'"'
                                    if result_string_one in number_correction:
                                        if result_string_two in number_correction:
                                            
                                            # Set for sure right father number
                                            for search_for_father in file_line_edit:
                                                father_string = '.addChild("'+str(child_string_split[1-line_adder])+'"'
                                                if father_string in search_for_father:
                                                    child_of_child_of_number = int(re.search(r'\d+', search_for_father).group())
    
                                            correction = number_correction.replace("modelPartData.","modelPartData"+str(child_of_child_of_number)+".")
                                            file_line_edit[file_line_edit.index(number_correction)] = correction
    except:
        print("Something went wrong while child refactoring")
                                
                                
    # Filter empty elements
    file_line_edit = list(filter(lambda item: item != "\n", file_line_edit))
    
    newfile = open(path.replace(".java","")+"CovertedModel.java", "w")
    newfile.writelines(file_line_edit)
    newfile.close()

    root.destroy()
    
btn = tk.Button(root, text ='Select File', command = lambda:open_file())#Button 
btn.grid(row=1, column=1) #Button Position
btn.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
tk.mainloop() #Mandatory for window