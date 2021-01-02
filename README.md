# cloud-IT-project Python 3.8
Period project for course Large Scale IT and Cloud Computing at UM DSAI 2020

## Group members:

- Elliot Doe
- Mariia Pliusnova
- Utku Arslan
- Thuyila Robinson
- Daan Stefens

## Project guide:

The project loads json files to get the needed information and the sample format of the files can be
found in the json package.

The following is the step-by-step guide for running the code:

1. Start by running server.py
2. Copy the IP address displayed in the terminal
3. Paste it in “SERVER = “paste here”“ in client.py 
4. Run client.py

    4.1 Possible options after running client.py:
    
        Type in option 1 or "Load":
        
        4.1.1 Possible options after selecting Load:
            Once User is selected:
                Json folder with all users configurations appear
                Select the Json file of the user preferred to be loaded

        4.1.2 Possible options after selecting the Json file:
                Load: load another user
                Select: select one of the connected users
                Connect: connect the loaded user to the server

    4.2 Possible initial options once connected:
    
        Load: load another user
        Select: select one of the connected users
        Send: send message to another user

            4.2.1 Possible options after selecting Send:
                    Send using ID -> type the ID to be sent to -> type message
                    Send using Name -> type the name to be sent to -> type message


        Disconnect: disconnect from the server
            4.2.2 Possible options after disconnection:
                    Load: load another user
                    Select: select one of the connected users
                    
    4.3 Possible options for connected user:
    
        Transfer: transfer money from the current user
            4.3.1 Possible options after selecting Transfer:
                    Type your account number (you can choose it from the organizations_config.json)
                    Enter your password (also in the same json file)
                    Type account to transfer to (also in the json file)
                    Enter the desired amount to be transferred
            4.3.2 Possible options after transfer:
                    Load, Select, Send, Disconnect, Transfer, Disbursal, Deposit, Make Account, Remove Account, Link

        Disbursal: withdraw money from this user’s account
            4.3.3 Possible options after selecting Disbursal:
                    Type your account number (you can choose it from the organizations_config.json)
                    Enter your password (also in the same json file)
                    Enter the desired amount of money to be withdrawn
            4.3.4 Possible options after disbursal:
                    Load, Select, Send, Disconnect, Transfer, Disbursal, Deposit, Make Account, Remove Account, Link

        Deposit: deposit money into the current user’s account
             4.3.5 Possible options after selecting Deposit:
                    Enter your account number (you can choose it from the organizations_config.json)
                    Enter your password (also in the same json file)
                    Enter the desired amount of money to be deposited
             4.3.6 Possible options after disbursal:
                    Load, Select, Send, Disconnect, Transfer, Disbursal, Deposit, Make Account, Remove Account, Link

        Make Account: create new account for the current user
             4.3.7 Possible options after selecting Make Account:
                    Enter your name
                    If name doesn’t exist:
                        Create a password
                    If name exists:
                        Possible options: 
                            Account confirmed (the account belongs to the current user):
                                Enter password (it’s in the json file)
                                Possible options if passwords match:
                                    Yes: add new account to the name
                                    No: don’t add a new account

                                Possible options if password doesn’t match:
                                    Load, Select, Send, Disconnect, Transfer, Disbursal, Deposit, Make Account, Remove Account, Link
                                    
                            Account not confirmed (the account doesn’t belong to the current users)
                                    Create a password
                                                             
             4.3.8 Possible options once an account has been created:
                    Load, Select, Send, Disconnect, Transfer, Disbursal, Deposit, Make Account, Remove Account, Link
                    
        Link: link the user to the organization
             4.3.9 Possible options after selecting Link:
                    Enter your id (it is listed as a personal_id in the organizations_config.json or
                    just as an id in the users config file)
                    Enter the company you work for(the name of the organization that a user belongs to)
                    If the full information is not provided:
                        It sends an error message
                    If everything check out:
                        Linking infromation is sent
                        If the information provided is in the organozation file:
                            The user is linked (this message is displayed in the server)
                        If not:
                            Invalid linking (this message is displayed in the server)
                            
             4.3.10 Possible options once the user is linked:
                    Load, Select, Send, Disconnect, Transfer, Disbursal, Deposit, Make Account, Remove Account, Link
        
    4.4 Possible options if the organization is selected to be loaded:
    
        4.4.1 Once Organization is selected:
            Json folder with all users configurations appear
            Select the Json file of the organization configuration to be loaded
            
        4.4.2 Possible options after selecting the Json file:
            Load: reload another organization configuration 
            Select: Select one of the organizations
            
        4.4.3 Possible options after selecting one of the organizations:
            Load: reload another organizations configurations
            Select: select another organization
            Connect: connect the selected organization to the server

        4.4.4 Possible options after connecting the selected organization
            Load: reload another organizations configurations
            Select: select another organization
            Connect: connect another selected organization to the server
            
 Role restrictions:
    
    In this project there is a sample ranking system, which is a following list(from lowest to highest rank):
        Employee -> 
        Manager -> 
        Executive -> 
