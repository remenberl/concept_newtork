#include "Network.h"
#include <fstream>
#include <iostream>
#include <string>

using namespace std;

string corpus_network_file = "../results/corpus_network.txt";
string wiki_network_file = "../results/wiki_network.txt";
string theta_file = "../results/theta.txt";
string gamma_file = "../results/gamma.txt";
string omega_file = "../results/omega.txt";

void write_output(double **theta, double **omega, double *gamma, int num_nodes, int num_topics)
{
	ofstream theta_output(theta_file, ofstream::out);
	if (theta_output.is_open()){
		for (int i = 1; i <= num_nodes; i++) {
			for (int r = 0; r < num_topics; r++) {
				theta_output << theta[i][r] << '\t';
			}
			theta_output << endl;
		}
		theta_output.close();
	}

	ofstream gamma_output(gamma_file, ofstream::out);
	if (gamma_output.is_open()){
		for (int i = 1; i <= num_nodes; i++) {
			gamma_output << gamma[i] << endl;
		}
		gamma_output.close();
	}

	ofstream omega_output(omega_file, ofstream::out);
	if (omega_output.is_open()){
		for (int r = 0; r < num_topics; r++) {
			for (int s = 0; s < num_topics; s++) {
				omega_output << omega[r][s] << '\t';
			}
			omega_output << endl;
		}
		omega_output.close();
	}
}

int main()
{
	int num_topics = 50;
	double lambda = 0.01;
	// corpus_network_file = "./test/1";
	// wiki_network_file = "./test/2";

	Network network = Network(corpus_network_file, wiki_network_file, num_topics, lambda);
	network.Initialize_Random_Links();
	for (int i = 1; i <= 300; i++) {
		network.Update(true);
		if (i >= 10 && i % (i / 10) == 0) {
			network.Refine();
			cout << "Refine Complete" << endl;
		}
		if (network.IsConvergent() == true) {
			cout << "Convergent after " << i << " update!" << endl;
			break;
		}
	}
	double **theta = network.GetTheta();
	double **omega = network.GetOmega();
	double *gamma = network.GetGamma();
	double num_nodes = network.GetNodeSize();

	write_output(theta, omega, gamma, num_nodes, num_topics);
}
