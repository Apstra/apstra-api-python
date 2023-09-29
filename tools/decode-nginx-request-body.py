
line = "{\x22application_points\x22:[{\x22id\x22:\x22fK731ak0Z73B5vZfSSA\x22,\x22policies\x22:[{\x22policy\x22:\x22d6d35349-cf19-4e39-9390-f11601f7a7c6\x22,\x22used\x22:true}]}]}"
print(bytes(line, 'utf-8').decode('unicode_escape'))