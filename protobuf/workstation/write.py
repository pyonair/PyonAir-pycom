import def_pb2

file = 'test'

sensor = def_pb2.Sensor()
sensor.id = 25
print(sensor)

serialized = sensor.SerializeToString()
print(serialized)

# f = open(file, 'wb')