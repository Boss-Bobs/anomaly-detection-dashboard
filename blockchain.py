# blockchain.py

import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
import time

class BlockchainService:
    def __init__(self):
        self.web3_provider = os.getenv(
            "WEB3_PROVIDER", 
            "wss://sepolia.infura.io/ws/v3/8742554fd5c94c549cb8b4117b076e7a"
        )
        self.contract_address = os.getenv(
            "CONTRACT_ADDRESS", 
            "0x279FcACc1eB244BBD7Be138D34F3f562Da179dd5"
        )
        self.contract_abi = [
            {
                "inputs": [
                    {"internalType": "string", "name": "_folder", "type": "string"},
                    {"internalType": "uint256", "name": "_frameIdx", "type": "uint256"},
                    {"internalType": "string", "name": "_error", "type": "string"}
                ],
                "name": "logAnomaly",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "stateMutability": "nonpayable",
                "type": "constructor"
            },
            {
                "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "name": "anomalies",
                "outputs": [
                    {"internalType": "string", "name": "folder", "type": "string"},
                    {"internalType": "uint256", "name": "frameIdx", "type": "uint256"},
                    {"internalType": "string", "name": "error", "type": "string"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "uint256", "name": "index", "type": "uint256"}],
                "name": "getAnomaly",
                "outputs": [
                    {"internalType": "string", "name": "", "type": "string"},
                    {"internalType": "uint256", "name": "", "type": "uint256"},
                    {"internalType": "string", "name": "", "type": "string"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getAnomalyCount",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "owner",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }
        ] # Your ABI here
        
        self.w3 = None
        self.contract = None
        self._connect_with_retries(retries=5, delay=5)
    
    def _connect_with_retries(self, retries, delay):
        for i in range(retries):
            print(f"Attempting blockchain connection (Attempt {i+1}/{retries})...")
            try:
                if self.web3_provider.startswith("wss"):
                    self.w3 = Web3(Web3.WebsocketProvider(self.web3_provider))
                else:
                    self.w3 = Web3(Web3.HTTPProvider(self.web3_provider))
                
                if self.w3.is_connected():
                    self.contract = self.w3.eth.contract(
                        address=self.contract_address, 
                        abi=self.contract_abi
                    )
                    # Add middleware for POA networks like Sepolia
                    self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    print("Successfully connected to the blockchain!")
                    return
                else:
                    print("Connection failed, retrying...")
            except Exception as e:
                print(f"Connection attempt failed: {e}")
            
            time.sleep(delay)
        
        print("Failed to connect to the blockchain after multiple retries.")
        raise Exception("Failed to connect to the blockchain.")

    def is_connected(self):
        return self.w3 and self.w3.is_connected()
