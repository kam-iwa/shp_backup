import arcpy

files = arcpy.GetParameterAsText(0)
output = arcpy.GetParameterAsText(1)

output_file = open(output, 'w')

files_list = files.split(';')
for fil in files_list:
    arcpy.env.workspace = fil
    output_file.write('begin file\n')
    output_file.write('\tbegin name\n\t\t' + fil + '\n\tend name\n')
    spatial_ref = arcpy.Describe(fil).spatialReference
    output_file.write('\tbegin epsg\n\t\t' + str(spatial_ref.factoryCode) + '\n\tend epsg\n')
    output_file.write('\tbegin fields\n')
    field = arcpy.ListFields(fil)
    field_names = [f.name for f in arcpy.ListFields(fil)]
    
    for i in field:
        output_file.write(
            '\t\t' + str(i.name) + ';' + str(i.aliasName) + ';' + str(i.domain) + ';' + str(i.editable) +
            ';' + str(i.isNullable) + ';' + str(i.required) + ';' + str(i.length) + ';' +
            str(i.type) + ';' + str(i.scale) + ';' + str(i.precision) + '\n'
            )
        
    output_file.write('\tend fields\n')
    output_file.write('\tbegin data\n')
    
    cur = arcpy.SearchCursor(fil)
    
    for row in cur:
        output_file.write('\t\tbegin row\n')
        field_counter = 0
        for field in field_names:
            if arcpy.ListFields(fil)[field_counter].type == "Geometry":
                output_file.write('\t\t\tbegin geometry\n')
                fname = arcpy.ListFields(fil)[field_counter]
                output_file.write('\t\t\t\t' + row.Shape.type + '\n')
                output_file.write('\t\t\t\tbegin coordinates\n')
                for i in range (0, row.Shape.partCount):
                    output_file.write('\t\t\t\t\tbegin part\n')
                    if row.Shape.type != 'point' and row.Shape.type != 'multipoint':
                        for j in row.Shape.getPart(i):
                            output_file.write('\t\t\t\t\t\t' + str(j).replace(',','.').replace(' ',';') + '\n')
                    else:
                        output_file.write('\t\t\t\t\t\t' + str(row.Shape.getPart(i)).replace(',','.').replace(' ',';') + '\n')
                    output_file.write('\t\t\t\t\tend part\n')
                output_file.write('\t\t\t\tend coordinates\n')
                output_file.write('\t\t\tend geometry\n')
            else:
                fieldval = repr(row.getValue(field))
                if fieldval[0:2] == "u'":
                    fieldval = fieldval[1:].decode("utf-8")
                output_file.write('\t\t\t' + fieldval + '\n')
            field_counter += 1
        output_file.write('\t\tend row\n')
    del row, cur
    output_file.write('\tend data\n')
    output_file.write('end file\n')
    arcpy.AddMessage('Ukonczono zapis pliku '+fil+' do kopii zapasowej.')


output_file.close()
