/**
    Simple script to automate the retrieval of the current account balance, in FLOW tokens, for the account with the address provided as argument.

    @param recipient (Address) The account address whose balance is to be retrieved from.

    @return {String: UFix64} Flow accounts have two balance values: a "default" one and an "available" one. The default shows the absolute account balance in FLOW tokens, while the available balance relates to the number of FLOW tokens that available to be moved. Cadence documentation describe these account properties as:
    
    account.balance -> The FLOW balance of the default vault of this account.
    account.availableBalance -> The FLOW balance of the default vault of this account that is available to be moved.
    
    This function returns a result dictionary in the format
    {
        "default": <UFix64>,
        "available": <UFix64>
    } 
**/

access(all) fun main(recipient: Address): {String: UFix64} {
    // Get a public reference to the account
    let accountRef: &Account = getAccount(recipient)

    var account_balance: {String: UFix64} = {}

    account_balance["default"] = accountRef.balance
    account_balance["available"] = accountRef.availableBalance

    // Log the values as well to make it more practical to analyse
    log(
        "Account "
        .concat(recipient.toString())
        .concat(" balance:\ndefault = ")
        .concat(account_balance["default"]!.toString())
        .concat(" FLOW.\navailable = ")
        .concat(account_balance["available"]!.toString())
        .concat(" FLOW.")
    )

    return account_balance
}