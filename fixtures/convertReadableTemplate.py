import json

def convertTemplate():
    pages = []
    with open('fixtures/readableTemplate.json', 'r') as json_file:
        pages = json.load(json_file)

    newDict = []

    pkIndex = len(pages) + 1

    for i in range(1, len(pages) + 1):
        page = pages[i - 1]
        newDict.append({
            "model": "sitemap.PAGE",
            "pk": i,
            "fields": {
                "title": page["stepTitle"],
                "betweenStepOperation": page["betweenStepOperation"],
                "operationType": page["operationType"]
            }})
        for option in page["options"]:

            optionDescription = option["description"]
            optionPk = pkIndex
            pkIndex += 1

            translatedType = "" 
            if option["type"] == "Dropdown":
                translatedType = "DDN"
            elif option["type"] == "Slider":
                translatedType = "SLD"
            else:
                raise Exception("Did not recognize option type for option " + optionDescription) 

            optionDict = {
                "model": "sitemap.OPTION",
                "pk": optionPk,
                "fields": {
                    "page": i,
                    "description": optionDescription,
                    "types": translatedType
                }
            }

            optionDict["fields"]["geoFile"] = option["file"] if "file" in option else ""
            optionDict["fields"]["attribute"] = option["attribute"] if "attribute" in option else None

            if "operation" in option:
                if option["operation"] == "=":
                    optionDict["fields"]["operation"] = "EQU"
                elif option["operation"] == ">=":
                    optionDict["fields"]["operation"] = "GOE"
                elif option["operation"] == "<=":
                    optionDict["fields"]["operation"] = "SOE"
                elif option["operation"] == ">":
                    optionDict["fields"]["operation"] = "STG"
                elif option["operation"] == "<":
                    optionDict["fields"]["operation"] = "STS"
            
            if translatedType == "SLD":
                optionDict["fields"]["minimum"] = option["minimum"]
                optionDict["fields"]["maximum"] = option["maximum"]
                optionDict["fields"]["step"] = option["step"]
                newDict.append(optionDict)
            elif translatedType == "DDN":
                newDict.append(optionDict)
                for choice in option["choices"]:
                    displayChoice = choice
                    codeChoice = choice
                    if type(choice) == list:
                        displayChoice = choice[0]
                        codeChoice = choice[1]

                    newDict.append({
                        "model": "sitemap.CHOICE",
                        "pk": pkIndex,
                        "fields" : {
                            "option": optionPk,
                            "choice": displayChoice,
                            "choiceCode": codeChoice
                        }
                    })
                    pkIndex += 1

    with open('fixtures/template.json', 'w') as outfile:
        json.dump(newDict, outfile)
        
            

        

if __name__ == '__main__':
    convertTemplate()


