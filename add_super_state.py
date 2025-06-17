#!/usr/bin/env python
import functools
import math
import os
import sys
import traceback
import inspect

class AddSuperState():

    def __init__(self, filename, name_superstate, selectedVertices, sm):
    
        sm.save_state_machine(filename)
    
    
    def SimpleStateMachine(self):
    
        #This code is too simple to manage all cases
        #So using the state machine UML is necessary
    
        # ------------------------------------------
        #              Get Lines
        # ------------------------------------------

        #If empty
        if filename == '':
            print("Error : data is not saved.")
            return
        
        #Read all lines
        sms_file = QFile(filename)
        sms_file.open(QIODevice.ReadOnly  | QIODevice.Text)
        states = {}
        currentState = ""
        
        #For each line
        while not sms_file.atEnd():
        
            #Get current line
            line = sms_file.readLine().data().decode("utf-8").strip()
            
            #if line is not empty
            if len(line) > 0:
                #If a state
                if '=' in line:
                    #Clean equal and a new state
                    currentState = line.replace("=", "")
                    states[currentState] = []
                #If a dependencies
                elif "->" in line:
                    #Clean equal
                    depend = line.replace("->", "")
                    states[currentState].append(depend)
        
        #Close file
        sms_file.close()
        
        # ------------------------------------------
        #              Add Super State
        # ------------------------------------------

        #Write all lines
        sms_file = QFile(filename)
        sms_file.open(QIODevice.WriteOnly)
        
        #For each state
        for state in states:
            #Init string
            sms_file.write("=" + state + "=" + "\n")
            #For each dependencies
            for d in states[state]:
                #Add dependency
                sms_file.write("->" + d + "\n")
            
        #Close file
        sms_file.close()        

