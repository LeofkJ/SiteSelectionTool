import json

def convertTemplate():
    pages = []
    with open('readableTemplate.json') as json_file:
        pages = json.load(json_file)

    newDict = []

    pkIndex = len(pages) + 1

    for i in range(1, len(pages) + 1):
        page = pages[i - 1]
        newDict.append({
            "model": "sitemap.PAGE",
            "pk": i,
            "fields": {
                "title": page["stepTitle"]
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
            
            if translatedType == "SLD":
                optionDict["fields"]["minimum"] = option["minimum"]
                optionDict["fields"]["maximum"] = option["maximum"]
                optionDict["fields"]["step"] = option["step"]
                newDict.append(optionDict)
            elif translatedType == "DDN":
                newDict.append(optionDict)
                for choice in option["choices"]:
                    newDict.append({
                        "model": "sitemap.CHOICE",
                        "pk": pkIndex,
                        "fields" : {
                            "option": optionPk,
                            "choice": choice
                        }
                    })
                    pkIndex += 1

    with open('template.json', 'w') as outfile:
        json.dump(newDict, outfile)
        
            

        

if __name__ == '__main__':
    convertTemplate()


