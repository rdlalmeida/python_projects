/*
    Use this transaction to fund the following emulator test accounts:

    account01: 0x179b6b1cb6755e31
    account02: 0xf3fcd2c1a78f5eee
    account03: 0xe03daebed8ca0615
    account04: 0x045a1763c93006ca
    account05: 0x120e725050340cab

    @param amount (UFix64) The amount of FLOW token to deposit in each account
    @param recipients ([Address]) The list of recipient addresses to deposit the funds into.

    NOTE: To execute this transaction using the flow-cli, use the following command:
    $ flow transactions send cadence/transactions/00_fund_all_accounts.cdc --args-json '[
        {
            "type": "Optional",
            "value": null
        }, 
        {
            "type": "Optional",
            "value": null
        }
    ]' --signer emulator-account --network emulator

    To execute this transaction with non-nil arguments, use
    $ flow transactions send cadence/transactions/00_fund_all_accounts.cdc --args-json '[
        {
            "type": "UFix64",
            "value": "1.0"
        },
        {
            "type": "Array",
            "value": [
                {
                    "type": "Address",
                    "value": "0x179b6b1cb6755e31"
                },
                {
                    "type": "Address",
                    "value": "0xf3fcd2c1a78f5eee"
                },
                {
                    "type": "Address",
                    "value": "0xe03daebed8ca0615"
                },
                {
                    "type": "Address",
                    "value": "0x045a1763c93006ca"
                },
                {
                    "type": "Address",
                    "value": "0x120e725050340cab"
                }
            ]
        }
    ]' --signer emulator-account --network emulator 
*/

import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7

transaction(amount: UFix64?, recipients: [Address]?) {
    let vaultReference: auth(FungibleToken.Withdraw) &FlowToken.Vault
    let receiverRef: [&{FungibleToken.Receiver}]
    let from: Address
    let to: [Address]
    let amount: UFix64

    prepare(signer: auth(BorrowValue) &Account) {
        self.from = signer.address

        self.vaultReference = signer.storage.borrow<auth(FungibleToken.Withdraw) &FlowToken.Vault>(from: /storage/flowTokenVault) ??
        panic(
            "Unable to get a reference to the vault for account ".concat(signer.address.toString())
        )
        if (amount == nil) {
            self.amount = 1.0
        }
        else {
            self.amount = amount!
        }

        self.receiverRef = []

        if (recipients == nil) {
            self.to = [0x179b6b1cb6755e31, 0xf3fcd2c1a78f5eee, 0xe03daebed8ca0615, 0x045a1763c93006ca, 0x120e725050340cab]
        }
        else{
            self.to = recipients!
        }


        for receiverAddress in self.to {
            let recipientAccount: &Account = getAccount(receiverAddress)

            self.receiverRef.append(recipientAccount.capabilities.borrow<&{FungibleToken.Receiver}>(/public/flowTokenReceiver) ?? panic(
                "Unable to retrieve a &{FungibleToken.Receiver} from ".concat(receiverAddress.toString())
            ))
        }
    }

    execute {
        for index, receiver in self.receiverRef {
            let tempVault: @{FungibleToken.Vault} <- self.vaultReference.withdraw(amount: self.amount)

            receiver.deposit(from: <- tempVault)

            log(
                "Transferred "
                .concat(self.amount.toString())
                .concat(" FLOW from account ")
                .concat(self.from.toString())
                .concat(" to ")
                .concat(self.to[index].toString())
            )
        }
    }
}