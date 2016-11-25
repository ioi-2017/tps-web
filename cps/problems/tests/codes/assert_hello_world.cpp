#include <iostream>
#include <cassert>
#include <fstream>

using namespace std;

int main(int *argc, char **argv)
{
    ifstream fin(argv[1]);
    string s;
    getline(fin, s);
    assert(s == "Hello World");
}
