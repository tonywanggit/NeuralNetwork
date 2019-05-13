def sub_fun(main_int):
    print("sub_fun", main_int)
    main_int = 2
    print("sub_fun", main_int)


if __name__ == '__main__':
    main_int = 1
    sub_fun(main_int)
    print("main", main_int)
