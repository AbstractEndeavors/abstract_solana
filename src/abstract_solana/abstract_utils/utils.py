def ifListGetSection(listObj,section=0):
    if isinstance(listObj,list):
        if len(listObj)>section:
            return listObj[section]
    return listObj
def if_list_get_Part(obj,i=0):
    if obj and isinstance(obj,list) and len(obj)>i:
        obj = obj[i]
    return obj
def updateData(data,**kwargs):
  data.update(kwargs)
  return data
def isListZero(obj):
    if obj and isinstance(obj, list):
        return obj[0]
    return obj
