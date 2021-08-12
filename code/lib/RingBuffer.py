import os
import _thread
from Constants import RING_BUFFER_FILE , RING_BUFFER_DIR
import ustruct
import ujson

# def ringBufferThread(config, logger):
#     # path, file_name, cell_number, cell_size

class RingBuffer:

    def __init__(self, path, file_name, cell_number, cell_size,  config, logger):

        self.logger = logger
        self.config = config
        self.logger.info("Creating/opening buffer....")
        self.file_path = path + file_name
        self.cell_number = cell_number
        self.cell_size = cell_size

        self.size_address = 0
        self.head_address = 1 * self.cell_size
        self.tail_address = 2 * self.cell_size
        self.buffer_start = 3 * self.cell_size
        self.buffer_end = (self.cell_number + 3) * self.cell_size

        self.head = self.buffer_start
        self.tail = self.buffer_start

        self.buffer_lock = _thread.allocate_lock()

        with self.buffer_lock:
            if file_name not in os.listdir(path[:-1]):  # if file does not exist, create one with details
                self.logger.error("Cannot find buffer file -- will make one")
                self.make_file()
            else:
                try:
                    if os.stat(self.file_path)[6] < (self.cell_number + 3) * self.cell_size:  # if file is too small
                        self.logger.error("Buffer parameters are incorrect")
                        self.make_file()
                    with open(self.file_path, 'r+b') as f:

                        # Check if file has the right dimensions
                        f.seek(self.size_address)
                        buffer_line = f.read(self.cell_size).decode()
                        index = buffer_line.find("\n")
                        if index == -1:
                            self.logger.error("Buffer parameters are incorrect")
                            self.make_file()
                        else:
                            size_lst = buffer_line[:index].split(',')
                            if int(size_lst[0]) != self.cell_number or int(size_lst[1]) != self.cell_size:
                                self.logger.error("Buffer parameters are incorrect")
                                self.make_file()

                        # Get current head
                        f.seek(self.head_address)
                        buffer_line = f.read(self.cell_size).decode()
                        index = buffer_line.find("\n")
                        if index == -1:
                            self.logger.error("Buffer parameters are incorrect")
                            self.make_file()
                        else:
                            self.head = int(buffer_line[:index])

                        # Get current tail
                        f.seek(self.tail_address)
                        buffer_line = f.read(self.cell_size).decode()
                        index = buffer_line.find("\n")
                        if index == -1:
                            self.logger.error("Buffer parameters are incorrect")
                            self.make_file()
                        else:
                            self.tail = int(buffer_line[:index])

                except Exception as e:
                    self.logger.exception("Buffer file is corrupted")
                    self.make_file()

    def make_file(self):
        self.logger.info("Flashing new buffer file...")
        self.logger.info("This can take a while, please do not turn off")

        try:
            os.remove(self.file_path)
        except Exception as e:
            pass

        with open(self.file_path, 'wb') as f:
            for val in range(self.cell_number + 3):
                f.write((self.cell_size * "0").encode())
            f.seek(self.size_address)
            f.write((str(self.cell_number) + ',' + str(self.cell_size) + "\n").encode())
            f.seek(self.head_address)
            f.write((str(self.head) + "\n").encode())
            f.seek(self.tail_address)
            f.write((str(self.tail) + "\n").encode())

    def push(self,objList):

    #f.write(ujson.dumps(self.configuration)

    #def write(self, line):  # writes line at head
        with self.buffer_lock:
            with open(self.file_path, 'r+b') as f:
                f.seek(self.head)
                ujson.dump(objList,f)
                #byteArray = ustruct.pack(formatStr,*objList)
                #f.write(formatStr + ",")
                #f.write(byteArray) # write line  ####(line + "\n").encode() str(formatStr + "," +    + "\n")
                f.write("\n")
                #print("write done" + str(objList))
                # check if buffer reached around
                next_head = self.head + self.cell_size
                if next_head >= self.buffer_end:
                    next_head = self.buffer_start  # loop around if end is reached
                if next_head == self.tail: #buffer full, remove oldest
                    self.tail += self.cell_size  # increment tail
                    if self.tail >= self.buffer_end:  # loop around if beginning is reached
                        self.tail = self.buffer_start
                    f.seek(self.tail_address) #persist tail pointer
                    f.write((str(self.tail) + "\n").encode()) #why string????

        #with self.buffer_lock: # Looks like a bug???
            #with open(self.file_path, 'r+b') as f:
                self.head += self.cell_size  # increment head
                if self.head >= self.buffer_end:
                    self.head = self.buffer_start  # loop around if end is reached
                f.seek(self.head_address)
                f.write((str(self.head) + "\n").encode())  # save new head
        #self.logger.debug("".join([ str(self.head),str(self.tail),str(self.cell_size)]))

    def read(self, read_tail=False):  # reads line at head or tail
        if self.tail is not self.head:  # if buffer is empty do not read line
            with self.buffer_lock:
                with open(self.file_path, 'r+b') as f:
                    if read_tail:
                        f.seek(self.tail)
                    else:
                        if self.head == self.buffer_start: #case where we are at buffer 0 , next time is at buffer N
                            f.seek(self.buffer_end - self.cell_size)
                        else:
                            f.seek(self.head - self.cell_size)
                    buffer_line = f.read(self.cell_size).decode()
                    index = buffer_line.find("\n")
                    print(buffer_line[:index])
                    if index == -1:

                        raise Exception("Data not found")
                    return buffer_line[:index]
        else:
            return None
            #raise Exception("Buffer is empty") #TODO: excpetion it too expensive, return None

    def pop(self, readTail=False): ## Returns head and deletes it. / default pop head, but cna do tail

        if self.tail is not self.head:  # if buffer is empty do not read line
            with self.buffer_lock:
                with open(self.file_path, 'r+b') as f:
                    if readTail:
                        f.seek(self.tail)
                    else:
                        if self.head == self.buffer_start:
                            f.seek(self.buffer_end - self.cell_size)
                        else:
                            f.seek(self.head - self.cell_size)
                    buffer_line =  f.read(self.cell_size).decode()
                    #print(buffer_line)
                    index = buffer_line.find("\n")
                    if index == -1: #When would this be the case? assume empty message?
                        #raise Exception("Data not found")
                        return None

                    #print(index)
                    data = ujson.loads(buffer_line[:index])
                    #print(data)
                    #obj = ustruct.unpack("<BHHHHH", data)
                    #print(obj)


                    #remove
                    if readTail:
                        #remove tail
                        self.tail += self.cell_size  # increment tail
                        if self.tail >= self.buffer_end:  # loop around if beginning is reached
                            self.tail = self.buffer_start
                        f.seek(self.tail_address)
                        f.write((str(self.tail) + "\n").encode()) #TODO: too many SD card writes for no reason , does value have to be null/o or can we ignore???
                    else:
                        #remove head
                        self.head -= self.cell_size  # decrement head
                        if self.head < self.buffer_start:  # loop around if beginning is reached
                            self.head = self.buffer_end - self.cell_size
                        f.seek(self.head_address)
                        f.write((str(self.head) + "\n").encode()) #TODO: investigate if this is needed, it causes a lot of IO - suspect this is persistance head/tail


                    return data #return all str before newline
        else:
            return None
            #raise Exception("Buffer is empty")



    def remove_head(self): #TODO: why no push pop?
        if self.tail is not self.head:  # if buffer is empty do not remove cell
            with self.buffer_lock:
                with open(self.file_path, 'r+b') as f:
                    self.head -= self.cell_size  # decrement head
                    if self.head < self.buffer_start:  # loop around if beginning is reached
                        self.head = self.buffer_end - self.cell_size
                    f.seek(self.head_address)
                    f.write((str(self.head) + "\n").encode())
        else:
            raise Exception("Buffer is empty") #why error , not just none?


    # def _removeTailNoLock(self):
    #     if self.tail is not self.head:  # if buffer is empty do not remove cell
    #     #with self.buffer_lock:
    #         with open(self.file_path, 'r+b') as f:
    #             self.tail += self.cell_size  # increment tail
    #             if self.tail >= self.buffer_end:  # loop around if beginning is reached
    #                 self.tail = self.buffer_start
    #             f.seek(self.tail_address)
    #             f.write((str(self.tail) + "\n").encode()) #TODO: too many SD car writes for no reason , does value have to be null/o or can we ignore???
    #     else:
    #         raise Exception("Buffer is empty")


    # def remove_tail(self):
    #     with self.buffer_lock:
    #        self._removeTailNoLock()


    def size(self, up_to=False):
        if not up_to:
            up_to = self.cell_number

        count = 0

        if self.tail is not self.head:  # if buffer is empty do not count
            while True:
                count += 1
                head_index = self.head - count * self.cell_size  # decrement cell by cell
                if head_index < self.buffer_start:
                    head_index = self.buffer_end - self.cell_size  # loop around
                if head_index == self.tail or count == up_to:  # if end of buffer or certain amount is found, then break
                    break

        return count
