#include <iostream>
#include <fstream>

using namespace std;

int main(int argc, char **argv)
{
    ifstream fin(argv[1]);
    ifstream fout(argv[2]);
    ifstream check_in(argv[3]);

    string s;
    getline(fin, s);

    string s2;
    getline(fout, s2);

    string s3;
    getline(check_in, s3);

    if (s == s2)
    {
        cout << 0 << endl;
        cerr << "Judge problem" << endl;
    }
    else if (s == s3)
    {
        cout << 0.5 << endl;
        cerr << "Output doesn't match the judge's output" << endl;
    }
    else if (s2 == s3)
    {
        cout << 1 << endl;
        cerr << "Correct Output" << endl;
    }
    else
    {
        cout << "Well this shouldn't be here" << endl;
        cerr << "This is OK though" << endl;
    }

}