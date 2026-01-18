/**
    Simple script to automate the retrieval of the current account storage capacity, in bytes, for the account with the address provided as argument

    @param recipient (Address) The account address whose storage capacity is to be retrieved from.

    @return {String: UInt64} Like with FLOW balance, Flow accounts have two types of account storage capacities: a "capacity" default one, and a "used" one. The "capacity" returns the absolute storage capacity in, in bytes, of the account. The "used" returns only the actual value used, also in bytes.

    account.storage.capacity -> The storage capacity of the account in bytes.

    account.storage.used -> The current amount of storage used by the account in bytes.

    This function returns a result dictionary in the format:
    {
        "capacity": <UInt64>,
        "used": <UInt64>
    }
**/

access(all) fun main(recipient: Address): {String: UInt64} {
    // 
    let accountRef: &Account = getAccount(recipient)

    var account_storage: {String: UInt64} = {}

    account_storage["capacity"] = accountRef.storage.capacity
    account_storage["used"] = accountRef.storage.used

    return account_storage
}






