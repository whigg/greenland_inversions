
import numpy as np
import os

# ---------------------------------------------------------------------------- #
def bufcount(filename):                                                        #
# ---------------------------------------------------------------------------- #
    '''
    '''
    f = open(filename)                  
    lines = 0
    buf_size = 1024 * 1024
    read_f = f.read # loop optimization
    buf = read_f(buf_size)
    while buf:
        lines += buf.count('\n')
        buf = read_f(buf_size)
    return lines



# ---------------------------------------------------------------------------- #
def get_variable(variable, directory, filename, partitions, verbose = False):  #
# ---------------------------------------------------------------------------- #
    """
    Read in a variable from output generated by Elmer

    Parameters:
    ==========

    variable:   name of the desired variable output by Elmer
    directory:  path to the files output by Elmer
    filename:   stem of the filename in `directory` where the results are
                    stored, e.g. "Test_Robin_Beta.result" for Fabien's code
    partitions: number of partitions of the underlying mesh

    Returns:
    =======
    data:       a packed numpy array consisting of the x, y, z locations of each
                    node of the mesh along with the values of the desired field
                    at each mesh point

    """

    dstart = np.zeros([2, partitions], dtype = np.int)

    parts_directory = (os.path.normpath(directory) + "/partitioning."
                            + str(partitions) + "/")

    # Get the lengths of all the node files
    file_lengths = [bufcount(parts_directory + "part." + str(p) + ".nodes")
                        for p in range(1, partitions + 1)]

    print(file_lengths)

    nn = sum(file_lengths)

    if verbose:
        print ("Total number of data points: {0}".format(nn))

    data = np.empty(nn,
                    dtype = [('node', np.int),
                             ('x', np.float64),
                             ('y', np.float64),
                             ('z', np.float64),
                             ('val', np.float64)]
                    )

    # For each partition,
    for p in range(partitions):
        if verbose:
            print ("Reading data for partition {0}".format(p))

        # find the location in the data array where we'll start writing
        start = sum(file_lengths[:p])

        # and open the .nodes file containing the location of each mesh point.
        node_file = open(parts_directory + "part." + str(p + 1) + ".nodes", "r")
        points = node_file.readlines()

        # Fill in all the geometry data stored in this partition's node file.
        for i in range(file_lengths[p]):
            node, _, x, y, z = points[i].split()
            data[start + i] = node, x, y, z, 0.0

        del points
        node_file.close()

        if verbose:
            print ("    Done reading geometry data")

        # Open the result file containing the data we're interested in
        data_file = open(os.path.normpath(directory)
                            + "/" + filename + "." + str(p), "r")

        # Find the line number within the result file where our field starts
        while 1:
            line = data_file.readline()
            if not line:
                break
            if variable in line:
                dstart[0, p] = dstart[1, p]
                dstart[1, p] = data_file.tell()

        data_file.seek(0)
        data_file.seek(dstart[0, p])
        line = data_file.readline()
        if line[6:] != "use previous\n":
            for i in range(file_lengths[p]):
                data_file.readline()

        for i in range(file_lengths[p]):
            data['val'][start + i] = float(data_file.readline())

        data_file.close()

        if verbose:
            print "    Done reading ", variable

    data = np.sort(data, order = ['x', 'y', 'z'])
    return data


# ---------------------------------------------------------------------------- #
def get_layer(data, surface = "top"):                                          #
# ---------------------------------------------------------------------------- #
    x = []
    y = []
    q = []

    argm = np.argmax
    if surface == "bottom":
        argm = np.argmin

    for x_val in np.unique(data['x']):
        x_p = data[ data['x'] == x_val ]
        for y_val in np.unique(x_p['y']):
            y_p = x_p[ x_p['y'] == y_val ]
            index = argm(y_p['z'])
            p = y_p[index]
            x.append(p[1])
            y.append(p[2])
            q.append(p[4])

    return np.asarray(x), np.asarray(y), np.asarray(q)


