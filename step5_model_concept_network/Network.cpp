#include "Network.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <ctime>

Network::Network(string undirected_network_file_path, string directed_network_file_path, int num_topics, double lambda)
:num_topics_(num_topics), lambda_(lambda), convergence_(false), likelihood_(numeric_limits<double>::lowest()), round_(0)
{
	cout << "Reading from network files including nodes and links." << endl;
	map<tuple<int, int>, int> link_index_map;
	string line;
  	ifstream undirected_network_file(undirected_network_file_path);
	if (undirected_network_file.is_open()){
	    while (getline(undirected_network_file, line)){
	    	vector<string> elements;
	    	stringstream s(line);
	    	string item;
		    while (std::getline(s, item, '\t'))
		        if (!item.empty())
		            elements.push_back(item);
	    	int node_i = std::stoi(elements[0]);
	    	int node_j = std::stoi(elements[1]);
	    	double weight = std::stoi(elements[2]);

	      	if (node_i >= node_j) swap(node_i, node_j);
	      	tuple<int, int> link = make_tuple(node_i, node_j);
	      	auto iter = link_index_map.find(link);
	      	if (iter == link_index_map.end()) {
	      		weighted_links_.push_back(make_tuple(node_i, node_j, lambda * weight));
	      		link_index_map[link] = weighted_links_.size() - 1;
	      	} else {
	      		get<2>(weighted_links_[iter->second]) += lambda * weight; 
	      	}
	    }
	    undirected_network_file.close();
	}

	map<tuple<int, int>, int> link_directed_weight_map;
  	ifstream directed_network_file(directed_network_file_path);
	if (directed_network_file.is_open()){
	    while (getline(directed_network_file, line)){
	    	vector<string> elements;
	    	stringstream s(line);
	    	string item;
		    while (std::getline(s, item, '\t'))
		        if (!item.empty())
		            elements.push_back(item);
	    	int node_i = std::stoi(elements[0]);
	    	int node_j = std::stoi(elements[1]);
	    	double weight = std::stoi(elements[2]);

	    	tuple<int, int> link = make_tuple(node_i, node_j);
	    	if (link_directed_weight_map.find(link) == link_directed_weight_map.end()) {
	      		link_directed_weight_map[link] = weight;
	      	} else {
	      		link_directed_weight_map[link] += weight;
	      	}

	      	if (node_i >= node_j) swap(node_i, node_j);
	      	link = make_tuple(node_i, node_j);
	      	auto iter = link_index_map.find(link);
	      	if (iter == link_index_map.end()) {
	      		weighted_links_.push_back(make_tuple(node_i, node_j, weight));
	      		link_index_map[link] = weighted_links_.size() - 1;
	      	} else {
	      		get<2>(weighted_links_[iter->second]) += weight;
	      	}
	    }
	    directed_network_file.close();
	}

	num_links_ = weighted_links_.size();
	cout << "Total links: " << num_links_ << endl;
	num_nodes_ = 0;
	for (auto iter = weighted_links_.begin(); iter != weighted_links_.end(); iter++) {
		if (get<1>(*iter) > num_nodes_) num_nodes_ = get<1>(*iter);
	}
	cout << "Total nodes: " << num_nodes_ << endl;
	theta_ = new double*[num_nodes_ + 1];
	for (int i = 0; i < num_nodes_ + 1; ++i)
    	theta_[i] = new double[num_topics_]();
	omega_ = new double*[num_topics_];
	for (int r = 0; r < num_topics_; ++r)
    	omega_[r] = new double[num_topics_]();
	gamma_ = new double[num_nodes_ + 1]();
	link_sum_ = new double[num_nodes_ + 1]();

	for (auto iter = weighted_links_.begin(); iter != weighted_links_.end(); iter++) {
		link_sum_[get<0>(*iter)] += get<2>(*iter);
		link_sum_[get<1>(*iter)] += get<2>(*iter);
	}
	for (int i = 1; i <= num_nodes_; i++) {
		link_sum_[0] += link_sum_[i];
		gamma_[i] = link_sum_[i];
	}

	gamma_[0] += link_sum_[0];
	for (int i = 1; i <= num_nodes_; i++) {
		gamma_[i] /= gamma_[0];
	}
}

Network::~Network()
{
	for(int i = 0; i < num_nodes_; ++i) {
	    delete [] theta_[i];
	}
	delete [] theta_;

	for(int r = 0; r < num_topics_; ++r) {
	    delete [] omega_[r];
	}
	delete [] omega_;

	delete [] gamma_;
	delete [] link_sum_;
}

void Network::Initialize_Random_Links()
{
	cout << "Initializing parameters." << endl;
	time_t seconds;
	time(&seconds);
    srand((unsigned int)seconds);

	double *af = new double[num_topics_ * num_topics_];	// for storing A_{ij}f_{ij}(r, s) temporarily

	vector<double> random_values(num_topics_ * num_topics_ + 1);
	random_values[0] = 0;
	for (auto iter_links = weighted_links_.begin(); iter_links != weighted_links_.end(); iter_links++) {
		random_values[num_topics_ * num_topics_] = get<2>(*iter_links);
		double normalizer = ((double)RAND_MAX + 1) / get<2>(*iter_links);
		for (int i = 1; i < num_topics_ * num_topics_; i++) {
			random_values[i] = ((double)rand() + 1) / normalizer;
		}
		// generate an ordered list of random values between 0 and A_{ij}
		sort(random_values.begin(), random_values.end());
		for (auto iter = random_values.begin(); iter != --random_values.end(); iter++) {
			af[iter - random_values.begin()] = *(iter + 1) - *(iter);
		}

		for (int r = 0; r < num_topics_; r++) {
			for (int s = 0; s < num_topics_; s++) {
				theta_[get<0>(*iter_links)][r] += af[r * num_topics_ + s];
				theta_[get<1>(*iter_links)][r] += af[s * num_topics_ + r];
				omega_[r][s] += af[r * num_topics_ + s] + af[s * num_topics_ + r];
			}
		}
	}
	delete [] af;

	double* omega_normalizer = new double[num_topics_]();
	for (int r = 0; r < num_topics_; r++) {
		for (int s = 0; s < num_topics_; s++) {
			omega_normalizer[r] += omega_[r][s];
		}
	}
	int good_topic_num = (int) (num_topics_ * 0.8); 
	for (int r = 0; r < good_topic_num; r++) {
		for (int s = 0; s < num_topics_; s++) {
			omega_[r][s] /= omega_normalizer[r] * omega_normalizer[s];
			omega_[r][s] *= link_sum_[0];
			if (r != s)
				omega_[r][s] /= 3;
			else
				omega_[r][s] *= 3;
		}
	}
	for (int r = good_topic_num; r <= num_topics_ - 1; r++) {
		for (int s = 0; s < num_topics_; s++) {
			omega_[r][s] /= omega_normalizer[r] * omega_normalizer[s];
			omega_[r][s] *= link_sum_[0];
			if (r != s)
				omega_[r][s] *= 3;
			else
				omega_[r][s] /= 3;
		}
	}
	delete [] omega_normalizer;

	for (int i = 1; i <= num_nodes_; i++) {
		for (int r = 0; r < num_topics_; r++) {
			theta_[i][r] /= link_sum_[i]; 
		}
	}
}

void Network::Refine()
{
	int changed = 0;
	for (int i = 0; i < num_nodes_ + 1; ++i) {
		double normalization = 0;
		int count = 0;
		double min = 1;
		int min_index = -1;
		for (int r = 0; r < num_topics_ ; ++r) {
			if (theta_[i][r] < 1.0 / num_topics_) {
				count += 1;
				if (theta_[i][r] < min && theta_[i][r] > 0) {
					min = theta_[i][r];
					min_index = r;
				}
			}
		}
		if (count > num_topics_ / 6 && min_index >= 0) {
			theta_[i][min_index] = 0;
			changed++;
			for (int r = 0; r < num_topics_; ++r) {
				normalization += theta_[i][r];
			}
			for (int r = 0; r < num_topics_; ++r) {
				theta_[i][r] /= normalization;
			}
		}
	}
	cout << changed << " nodes get refined." << endl;
}

void Network::Update(bool likelihood_flag = false)
{
	round_ += 1;
	if (convergence_ == true) {
		cout << "Already convergent!" << endl;
		return;
	}

	double new_likelihood = 0;
	double *af = new double[num_topics_ * num_topics_];	// for storing A_{ij}f_{ij}(r, s) temporarily
	double **new_theta = new double*[num_nodes_ + 1];
	for (int i = 0; i < num_nodes_ + 1; ++i)
    	new_theta[i] = new double[num_topics_]();
	double **new_omega = new double*[num_topics_];
	for (int r = 0; r < num_topics_; ++r)
    	new_omega[r] = new double[num_topics_]();

	for (auto iter_links = weighted_links_.begin(); iter_links != weighted_links_.end(); iter_links++) {
		double normalizer = 0;
		for (int r = 0; r < num_topics_; r++) {
			for (int s = 0; s < num_topics_; s++) {
				af[r * num_topics_ + s] = theta_[get<0>(*iter_links)][r] * omega_[r][s] * theta_[get<1>(*iter_links)][s];
				normalizer += af[r * num_topics_ + s];
			}
		}
		for (int r = 0; r < num_topics_; r++) {
			for (int s = 0; s < num_topics_; s++) {
				af[r * num_topics_ + s] *= get<2>(*iter_links) / normalizer;
			}
		}
		if (likelihood_flag == true) {
			new_likelihood += get<2>(*iter_links) * log(normalizer + 10e-9);
		}
		for (int r = 0; r < num_topics_; r++) {
			for (int s = 0; s < num_topics_; s++) {
				new_theta[get<0>(*iter_links)][r] += af[r * num_topics_ + s];
				new_theta[get<1>(*iter_links)][r] += af[s * num_topics_ + r];
				new_omega[r][s] += af[r * num_topics_ + s] + af[s * num_topics_ + r];
			}
		}
	}
	delete [] af;

	double* omega_normalizer = new double[num_topics_]();
	for (int r = 0; r < num_topics_; r++) {
		for (int s = 0; s < num_topics_; s++) {
			omega_normalizer[r] += new_omega[r][s];
		}
	}
	for (int r = 0; r < num_topics_; r++) {
		for (int s = 0; s < num_topics_; s++) {
			new_omega[r][s] /= omega_normalizer[r] * omega_normalizer[s];
			new_omega[r][s] *= link_sum_[0];
		}
	}
	delete [] omega_normalizer;

	for (int i = 1; i <= num_nodes_; i++) {
		for (int r = 0; r < num_topics_; r++) {
			new_theta[i][r] /= link_sum_[i];
		}
	}

	for(int i = 0; i < num_nodes_; ++i) {
	    delete [] theta_[i];
	}
	delete [] theta_;

	for(int r = 0; r < num_topics_; ++r) {
	    delete [] omega_[r];
	}
	delete [] omega_; 
	theta_ = new_theta;
	omega_ = new_omega;

	if (likelihood_flag == true) {
		if (fabs((new_likelihood - likelihood_) / (likelihood_ + 10e-9)) <= 10e-4) {
			convergence_ = true;
		}
		cout << "Round " << round_ << ", Likelihood: " << new_likelihood << " +" << fabs(new_likelihood - likelihood_) << endl;
		likelihood_ = new_likelihood;
	}
}

double* Network::GetGamma()
{
	return gamma_;
}

double** Network::GetOmega()
{
	return omega_;
}

double** Network::GetTheta()
{
	return theta_;
}

int Network::GetNodeSize()
{
	return num_nodes_;
}

bool Network::IsConvergent()
{
	return convergence_;
}
