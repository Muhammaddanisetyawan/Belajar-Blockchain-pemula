import sys
import hashlib
import json
from time import time
from uuid import uuid4
from flask import Flask, request, jsonify
import requests
from urllib.parse import urlparse

class Blockchain(object):
    difficulty_target = "0000"  # Kesulitan jaringan

    def hash_block(self, block):  # Perbaiki penamaan metode
        block_encode = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_encode).hexdigest()

    def __init__(self):
        self.chain = []
        self.current_transaction = []
        genesis_hash = self.hash_block("hash_block")

        self.append_block(
            hash_of_previous_block=genesis_hash,
            nonce=self.proof_of_work(0, genesis_hash, [])
        )

    def proof_of_work(self, index, hash_of_previous_block, transaction):
        nonce = 0
        while self.valid_proof(index, hash_of_previous_block, transaction, nonce) is False:
            nonce += 1
        return nonce

    def valid_proof(self, index, hash_of_previous_block, transaction, nonce):
        content = f'{index}{hash_of_previous_block}{transaction}{nonce}'.encode()
        content_hash = hashlib.sha256(content).hexdigest()
        return content_hash[:len(self.difficulty_target)] == self.difficulty_target

    def append_block(self, nonce, hash_of_previous_block):
        block = {
            'index': len(self.chain),
            'timestamp': time(),
            'transaction': self.current_transaction,
            'nonce': nonce,
            'hash_of_previous_block': hash_of_previous_block
        }
        self.current_transaction = []  # Reset transaksi saat ini
        self.chain.append(block)
        return block

    def add_transaction(self, sender, recipient, amount):
        self.current_transaction.append({
            'amount': amount,
            'recipient': recipient,
            'sender': sender
        })
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1] if self.chain else None

app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', "")  # Alamat pengirim
blockchain = Blockchain()

# Routes
@app.route('/blockchain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/mining', methods=['GET'])
def mine_block():
    blockchain.add_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1  # Reward untuk miner
    )
    last_block_hash = blockchain.hash_block(blockchain.last_block)
    index = len(blockchain.chain)
    nonce = blockchain.proof_of_work(index, last_block_hash, blockchain.current_transaction)
    block = blockchain.append_block(nonce, last_block_hash)

    response = {
        'message': "Block baru telah ditambahkan (mined)",
        'index': block['index'],
        'hash_of_previous_block': block['hash_of_previous_block'],
        'nonce': block['nonce'],
        'transaction': block['transaction']
    }
    return jsonify(response), 200

@app.route('/transaction/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required_fields = ['sender', 'recipient', 'amount']
    if not all(b in values for b in required_fields):
        return 'Missing fields', 400
    index = blockchain.add_transaction(
        values['sender'],
        values['recipient'],
        values['amount']
    )
    response = {'message': f'Transaksi akan ditambahkan ke block {index}'}
    return jsonify(response), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(sys.argv[1]))
