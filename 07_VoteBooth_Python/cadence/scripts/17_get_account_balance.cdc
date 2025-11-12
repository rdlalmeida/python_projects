/**
    Simple script to return the FLOW token balance of the account supplied as input.
    
    @param accountAddress (Address) The address of the account whose balance is to be retrieve.

    @returns (UFix64) The current balance of the account queried, in FLOW tokens.
**/

import FungibleToken from 0xee82856bf20e2aa6
import FlowToken from 0x0ae53cb6e3f42a79

access(all) fun main(accountAddress: Address): UFix64 {
    let currentAccount: &Account = getAccount(accountAddress)
    let balancePublicPath: PublicPath = /public/flowTokenBalance

    // Get the FLOW balance
    let balanceRef: &{FungibleToken.Balance} = currentAccount.capabilities.borrow<&{FungibleToken.Balance}>(balancePublicPath) ??
    panic(
        "Unable to retrieve a valid &{FungibleToken.Balance} at "
        .concat(balancePublicPath.toString())
        .concat(" for account ")
        .concat(accountAddress.toString())
    )
    
    return balanceRef.balance
}