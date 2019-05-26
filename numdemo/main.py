import multiprocessing as mp


def foo(i, k):
    for j in range(18000):
        r = 10 ** j
    print(i, k)

def mfoo():
    process_pool = []
    for i in range(10):
        process = mp.Process(target=foo, args=(i, i * 10))
        process.daemon = True
        process_pool.append(process)

    for process in process_pool:
        process.start()
    for process in process_pool:
        process.join()

if __name__ == '__main__':
    close_list = [1, 2, 3, 4]
    for i in range(1, len(close_list)):
        print(close_list[i])

    print(close_list[-1])