# neural network class definition

import numpy as np
import scipy.special

class NeuralNetwork:
    def __init__(self, inputnodes, hiddennodes, outputnodes, learningrate):
        self.inodes = inputnodes
        self.hnodes = hiddennodes
        self.onodes = outputnodes

        self.wih = np.random.normal(0.0, pow(self.hnodes, -0.5), (self.hnodes, self.inodes))
        self.who = np.random.normal(0.0, pow(self.onodes, -0.5), (self.onodes, self.hnodes))

        self.lr = learningrate

        self.activation_function = lambda x : scipy.special.expit(x)
        pass

    def train(self, input_list, target_list):
        inputs = np.array(input_list, ndmin=2).T
        targets = np.array(target_list, ndmin=2).T

        hidden_inputs = np.dot(self.wih, inputs)
        hidden_outputs = self.activation_function(hidden_inputs)

        final_inputs = np.dot(self.who, hidden_outputs)
        final_outputs = self.activation_function(final_inputs)

        output_errors = targets - final_outputs
        hidden_errors = np.dot(self.who.T, output_errors)

        self.who += self.lr * np.dot((output_errors * final_outputs * (1 - final_outputs)), np.transpose(hidden_outputs))
        self.wih += self.lr * np.dot((hidden_errors * hidden_outputs * (1- hidden_outputs)), np.transpose(inputs))
        pass

    def query(self, input_list: object) -> object:
        inputs = np.array(input_list, ndmin=2).T

        hidden_inputs = np.dot(self.wih, inputs)
        hidden_outputs = self.activation_function(hidden_inputs)

        final_inputs = np.dot(self.who, hidden_outputs)
        final_outputs = self.activation_function(final_inputs)

        return final_outputs

if __name__ == '__main__':
    input_nodes = 784
    hidden_nodes = 400
    output_nodes = 10
    learning_rate = 0.2

    neuralNetwork = NeuralNetwork(input_nodes, hidden_nodes, output_nodes, learning_rate)
    print("run nerual network")

    data_file = open("/usr/local/data/mnist_train_100.csv", "r")
    data_list = data_file.readlines()
    data_file.close()

    print(np.asfarray(data_list[0].split(',')[1:]))

    epochs = 2
    for e in range(epochs) :
        print("Start epoch: ", e)
        for record in data_list:
            all_values = record.split(',')
            inputs = (np.asfarray(all_values[1:]) / 255.0 * 0.99) + 0.01
            targets = np.zeros(output_nodes) + 0.01
            targets[int(all_values[0])] = 0.99
            neuralNetwork.train(inputs, targets)
            pass


    test_data_file = open("/usr/local/data/mnist_test_10.csv", "r")
    test_data_list = test_data_file.readlines()
    test_data_file.close()

    scordcard = []
    for test_record in test_data_list:
        test_all_values = test_record.split(',')
        test_output = neuralNetwork.query(np.asfarray(test_all_values[1:]))

        current_label = int(test_all_values[0])
        output_label = np.argmax(test_output)

        print(current_label, output_label)
        if (current_label == output_label):
            scordcard.append(1)
        else:
            scordcard.append(0)

    scordcard_array = np.asarray(scordcard)
    print(scordcard, scordcard_array)
    print("Performance = " , scordcard_array.sum() / scordcard_array.size)
