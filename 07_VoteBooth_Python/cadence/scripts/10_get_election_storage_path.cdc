/**
    This script automates the retrieval of the storage path where the Election identified with the electionId provided is stored in.

    @param electionId: (UInt64) The election identifier for the Election resource whose parameter is to be returned to.

    @returns (StoragePath) Returns the storage path for the Election in question, if it exists, as defined in the ElectionIndex. Otherwise, the process panics at the offending step.
**/
import ElectionStandard from 0xf8d6e0586b0a20c7
import VoteBooth from 0xf8d6e0586b0a20c7

access(all) fun main(electionId: UInt64): StoragePath {
    let deployerAccount: &Account = getAccount(VoteBooth.deployerAddress)

    let electionIndexRef: &{VoteBooth.ElectionIndexPublic} = deployerAccount.capabilities.borrow<&{VoteBooth.ElectionIndexPublic}>(VoteBooth.electionIndexPublicPath) ??
    panic(
        "Unable to get a valid &{VoteBooth.ElectionIndexPublic} at `VoteBooth.electionIndexPublicPath.toString()` from account `deployerAccount.address.toString()`"
    )
    
    let electionStoragePath: StoragePath = electionIndexRef.getElectionStoragePath(electionId: electionId) ??
    panic(
        "Unable to retrieve a valid StoragePath to the Election with id `electionId.toString()` from the ElectionIndex stored in account `deployerAccount.address.toString()`"
    )

    return electionStoragePath
}