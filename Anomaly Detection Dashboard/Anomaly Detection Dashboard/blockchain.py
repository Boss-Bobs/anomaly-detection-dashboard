import os
from web3 import Web3

class BlockchainService:
    """Service class to handle blockchain interactions."""
    
    def __init__(self):
        # Configuration from environment variables with fallbacks
        self.web3_provider = os.getenv("WEB3_PROVIDER", "https://sepolia.infura.io/v3/8742554fd5c94c549cb8b4117b076e7a")
        self.contract_address = os.getenv("CONTRACT_ADDRESS", "0x279FcACc1eB244BBD7Be138D34F3f562Da179dd5")
        
        # Contract ABI
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
        ]
        
        # Initialize Web3 connection
        self.w3 = None
        self.contract = None
        self._connect()
    
    def _connect(self):
        """Establish connection to the blockchain."""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.web3_provider))
            if not self.w3.is_connected():
                raise Exception("Failed to connect to Sepolia network")
            
            self.contract = self.w3.eth.contract(
                address=self.contract_address, 
                abi=self.contract_abi
            )
        except Exception as e:
            raise Exception(f"Blockchain connection failed: {str(e)}")
    
    def get_anomaly_count(self):
        """Get the total number of anomalies from the blockchain."""
        if not self.contract:
            raise Exception("Contract not initialized")
        
        return self.contract.functions.getAnomalyCount().call()
    
    def get_transaction_logs(self):
        """Fetch all transaction logs from the blockchain."""
        if not self.contract:
            raise Exception("Contract not initialized")
        
        anomaly_count = self.get_anomaly_count()
        tx_logs = []
        
        for i in range(anomaly_count):
            try:
                folder, frame_idx, error = self.contract.functions.getAnomaly(i).call()
                tx_logs.append({
                    "index": i,
                    "folder": folder,
                    "frame": frame_idx,
                    "error": error,
                    "timestamp": "2025-09-04 01:19"  # Using the timestamp from original code
                })
            except Exception as e:
                # Continue if one transaction fails
                continue
        
        return tx_logs
    
    def is_connected(self):
        """Check if the blockchain connection is active."""
        return self.w3 and self.w3.is_connected()
