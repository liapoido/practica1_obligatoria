from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
from random import random, randint


N = 100
K = 10
NPROD = 3

def delay(factor = 3):
    sleep(random()/factor)


def add_data(storage, index, data, mutex):
    mutex.acquire()
    try:
    	storage[index.value]=data
    	delay(6)
    	index.value=index.value + 1 
    finally:
        mutex.release()


def get_data(storage, index, mutex):
    mutex.acquire()
    try:
        data = storage[0]
        index.value = index.value - 1
        delay()
        for i in range(index.value):
            storage[i] = storage[i + 1]
        storage[index.value] = -1
    finally:
        mutex.release()
    return data

#each producer produces N random increasing numbers through randint
def producer(storage, index, empty, non_empty, mutex):
	data=randint(0,5)
	for v in range(N):
		print (f"producer {current_process().name} produciendo")
		delay(6)
		empty.acquire() #wait
		data+=randint(0,5)
		add_data(storage, index, data, mutex)
		non_empty.release() #signal
		print (f"producer {current_process().name} almacenado {v}")
	empty.acquire() #wait
	add_data(storage,index,-1,mutex) #produces -1 when it's done
	non_empty.release() #signal

#get the minimum value from the storages
def min_prod(storage):
	j=0
	while (storage[j][0]==-1):
		j+=1
	ind=j
	value=storage[j][0]
	for i in range(j, NPROD):
		if (storage[i][0]!=-1):
			if storage[i][0] < value:
				value=storage[i][0]
				ind=i
	return ind,value

#it says me if there still are producers that are producing
def haya_productores(storage):
	for i in range(NPROD):
		if (storage[i][0]!= -1):
			return True
	return False

#the consumer waits for each producer to produce at least a number
#and then starts stocking it in a list by choosing always the minimum one
def consumer(storage, index, empty, non_empty, mutex,storage_sort):
    for i in range(NPROD):	
    	non_empty[i].acquire()
    j=0
    while haya_productores(storage):
    	print (f"consumer desalmacenando")
    	ind,value = min_prod(storage)
    	get_data(storage[ind],index[ind],mutex[ind])
    	storage_sort[j]=value #storing the mininum value on the list
    	j+=1
    	empty[ind].release() #signal
    	print (f"consumer consumiendo {value}")
    	non_empty[ind].acquire() #wait
    	delay()
    print(storage_sort[:])

def main():
	#creating lists of buffers, index and semaphores for the producers
	#and the list for the sorted numbers	
    storage = [ Array('i', K) for _ in range(NPROD)]
    storage_sort = Array('i', N*NPROD)
    index = [ Value('i', 0) for _ in range(NPROD)]
    for j in range(NPROD):
    	for i in range(K):
    		storage[j][i] = -1
    	print ("almacen inicial", storage[j][:], "indice", index[j].value)
	
	
    non_empty = [Semaphore(0) for _ in range(NPROD)]
    empty = [BoundedSemaphore(K) for _ in range(NPROD)]
    mutex = [Lock() for _ in range(NPROD)]

    prodlst = [ Process(target=producer,
                        name=f'prod_{i}',
                        args=(storage[i], index[i], empty[i], non_empty[i], mutex[i]))
                for i in range(NPROD) ]

    conslst = [ Process(target=consumer,
                      name=f"cons_{i}",
                      args=(storage, index, empty, non_empty, mutex,storage_sort))]

    for p in prodlst + conslst:
        p.start()

    for p in prodlst + conslst:
        p.join()


if __name__ == '__main__':
    main()