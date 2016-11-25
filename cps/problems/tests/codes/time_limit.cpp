#include <iostream>

using namespace std;

int main()
{
    for (int i = 1; ; i++)
    {
        cout << i << endl;
        for (int j = 1; j < 100000000; j++)
            if (j % ((j % 2) + 1) == 10)
                cout << "This will not be printed" << endl;
    }
}
