#include <iostream>
#include <string>
#include <tuple>
#include <vector>

using namespace std;

class Network {
	private:
		int num_nodes_;
		int num_links_;
		int num_topics_;
		int round_;
		double lambda_;
		vector<tuple<int, int, double>> weighted_links_;
		double **omega_;
		double *gamma_;
		double **theta_;
		double *link_sum_;
		double likelihood_;
		bool convergence_;

	public:
		Network(string undirected_network_file_path, string directed_network_file_path, int num_topic, double lambda);
		~Network();
		void Initialize_Random_Links();
		void Initialize_Random_Nodes(string);
		void Update(bool);
		void Refine();
		double* GetGamma();
		double** GetOmega();
		double** GetTheta();
		int GetNodeSize();
		bool IsConvergent();
};