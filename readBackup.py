import arcpy
import math
import datetime
import copy

input_txt = arcpy.GetParameterAsText(0)
output_txt = arcpy.GetParameterAsText(1)

input_file = open(input_txt, 'r')

file_lines = []

for line in input_file:
    file_lines.append(line.strip())

input_file.close()

arcpy.AddMessage("Wykryto "+str(file_lines.count('begin file'))+" plikow w kopii zapasowej.")
if file_lines.count('begin file') == 0:
    arcpy.AddError("BLAD : Brak plikow w kopii zapasowej. Program konczy dzialanie!")

files_list = []

for i in range(0,file_lines.count('begin file')):
    begin = file_lines.index('begin file')
    end = file_lines.index('end file')
    files_list.append(file_lines[begin+1:end])
    file_lines = file_lines[end+1:]

del file_lines

file_data = []

for fil in files_list:
    
    begin = {
        'name' : fil.index('begin name'),
        'epsg' : fil.index('begin epsg'),
        'fields' : fil.index('begin fields'),
        'data' : fil.index('begin data')
        }
    end = {
        'name' : fil.index('end name'),
        'epsg' : fil.index('end epsg'),
        'fields' : fil.index('end fields'),
        'data' : fil.index('end data')
        }
    
    name = fil[begin['name']+1:end['name']][0]

    epsg = int(fil[begin['epsg']+1:end['epsg']][0])
    
    fields = fil[begin['fields']+1:end['fields']]
    for field in range(0, len(fields)):
        fields[field] = fields[field].split(';')
        field_values = fields[field]
        for i in range(0, len(field_values)):
            if i == 3 or i == 4 or i == 5:
                if field_values[i] == "True":
                    field_values[i] = True
                else:
                    field_values[i] = False
            elif i == 6 or i == 8 or i == 9:
                field_values[i] = int(field_values[i])
        field_dict = {
                'name':field_values[0],
                'alias':field_values[1],
                'domain':field_values[2],
                'editable':field_values[3],
                'nullable':field_values[4],
                'required':field_values[5],
                'length':field_values[6],
                'type':field_values[7],
                'scale':field_values[8],
                'precision':field_values[9]
            }
        fields[field] = field_dict
    
    
    data = fil[begin['data']+1:end['data']]
    data_list = []
    for rows in range(0, data.count('begin row')):
        begin_row = data.index('begin row')
        end_row = data.index('end row')
        row_data = data[begin_row+1:end_row]

        begin_geo = row_data.index('begin geometry')
        end_geo = row_data.index('end geometry')
        row_data[begin_geo] = row_data[begin_geo+1:end_geo]
        del row_data[begin_geo+1:end_geo+1]
        
        coords_data = row_data[begin_geo]
        begin_coords = coords_data.index('begin coordinates')
        end_coords = coords_data.index('end coordinates')
        coords_data[begin_coords] = coords_data[begin_coords+1:end_coords]
        del coords_data[begin_coords+1:end_coords+1]

        parts_data = coords_data[begin_coords]
        for part in range(0, parts_data.count('begin part')):
            begin_part = parts_data.index('begin part')
            end_part = parts_data.index('end part')
            parts_data[begin_part] = parts_data[begin_part+1:end_part]
            del parts_data[begin_part+1:end_part+1]
            part_length = len(parts_data[begin_part])
            for i in range(0, part_length):
                if parts_data[begin_part][i] != 'None':
                    parts_data[begin_part][i] = parts_data[begin_part][i].split(';')
                    try:
                        x = float(parts_data[begin_part][i][0])
                        if math.isnan(x):
                            x = None
                    except ValueError:
                        x = None
                    try:
                        y = float(parts_data[begin_part][i][1])
                        if math.isnan(y):
                            y = None
                    except ValueError:
                        y = None
                    try:
                        z = float(parts_data[begin_part][i][2])
                        if math.isnan(z):
                            z = None
                    except ValueError:
                        z = None
                    try:
                        m = float(parts_data[begin_part][i][3])
                        if math.isnan(m):
                            m = None
                    except ValueError:
                        m = None
                    parts_data[begin_part][i] = {
                            'x':x,
                            'y':y,
                            'z':z,
                            'm':m
                        }
                else:
                    parts_data[begin_part][i] = {
                            'x':None,
                            'y':None,
                            'z':None,
                            'm':None
                        }

        geom_defined = False
        for i in range(0, len(row_data)):
            if isinstance(row_data[i], list):
                if geom_defined == False:
                    geometry_type = row_data[i][0]
                    geom_defined = True
                row_data[i] = {
                        'type':row_data[i][0],
                        'coordinates':row_data[i][1]
                    }
            else:
                row_data[i] = eval(row_data[i])
                    
        data_list.append(row_data)
        del data[begin_row:end_row+1]
            
    data = data_list
    del data_list

    file_data.append({
        'name' : name,
        'epsg' : epsg,
        'fields' : fields,
        'data' : data,
        'geometry_type' : geometry_type
        })

    arcpy.AddMessage("Ukonczono wczytywanie danych z kopii zapasowej dla pliku " + name)
    

if '\\' in output_txt:
    index = output_txt.rindex('\\')
else:
    index = output_txt.rindex('/')
        
arcpy.env.workspace = output_txt[:index]

arcpy.CreateFolder_management(output_txt[:index], output_txt[index:])

arcpy.env.workspace = output_txt


for fil in file_data:
    if '\\' in fil['name']:
        file_loc = fil['name'].split('\\')
    else:
        file_loc = fil['name'].split('/')

    filename = file_loc[-1]

    reference = arcpy.SpatialReference(fil['epsg'])

    if fil['epsg'] != 0:
        arcpy.CreateFeatureclass_management(arcpy.env.workspace,filename,fil['geometry_type'], spatial_reference = reference)
    else:
        arcpy.CreateFeatureclass_management(arcpy.env.workspace,filename,fil['geometry_type'])

    cur = arcpy.InsertCursor(filename)
    for i in range(0, len(fil['data'])):
        row = cur.newRow()
        cur.insertRow(row)

    del row, cur
    file_field_list = arcpy.ListFields(filename)
    file_fieldname_list = [i.name for i in file_field_list]
    data_fieldname_list = [i['name'] for i in fil['fields']]

    field_list = []
    for field in fil['fields']:
        field_list.append(field['name'])
        if field['type'] != 'OID' and field['type'] != 'Geometry':
            arcpy.AddField_management(filename, field['name'], field['type'], field['precision'],
                                      field['scale'], field['length'], field['alias'],
                                      field['nullable'], field['required'], field['domain'])

    for i in file_fieldname_list:
        if i not in data_fieldname_list:
            arcpy.DeleteField_management(filename, i)

    file_field_list = arcpy.ListFields(filename)
    file_fieldname_list = [i.name for i in file_field_list]
    data_fieldname_list = [i['name'] for i in fil['fields']]

    cur = arcpy.UpdateCursor(filename)
    row_counter = 0
    for row in cur:
        field_counter = 0
        for i in fil['data'][row_counter]:
            if fil['fields'][field_counter]['type'] != 'Geometry' and fil['fields'][field_counter]['type'] != 'OID':
                row.setValue(file_fieldname_list[field_counter], i)
            elif fil['fields'][field_counter]['type'] == 'Geometry':
                points = arcpy.Array()
                for j in i['coordinates']:
                    part = arcpy.Array()
                    for k in j:
                        if k['x'] != None and k['y'] != None:
                            pt = arcpy.Point(k['x'], k['y'], k['z'], k['m'])
                            part.add(pt)
                    points.add(part)
                if i['type'] == 'polygon':
                    geometria = arcpy.Polygon(points)
                elif i['type'] == 'polyline':
                    geometria = arcpy.Polyline(points)
                elif i['type'] == 'point':
                    geometria = arcpy.PointGeometry(pt)
                elif i['type'] == 'multipoint':
                   geometria = arcpy.Multipoint(points)
                else:
                    arcpy.AddError('Typ geometrii niewspierany przez program. Program konczy dzialanie.')
                row.setValue(file_fieldname_list[field_counter], geometria)
                cur.updateRow(row)

            field_counter += 1
        cur.updateRow(row)
        row_counter += 1
    del row, cur
    arcpy.AddMessage("Ukonczono zapis danych z kopii zapasowej dla pliku " + filename)

