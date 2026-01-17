/**
    This script returns a public resource reference to a Election instance, i.e., affected by the ElectionStandard.ElectionPublic resource interface.

    @param electionId (UInt64): The election identifier for the Election whose reference is to be retrieved.
    
    @return (&{ElectionStandard.ElectionPublic}): If an Election exists for the electionId provided and has a public capability published properly, this script returns the public resource borrowed from the Election instance. Otherwise returns nil
**/
import ElectionStandard from 0xf8d6e0586b0a20c7
import VoteBooth from 0xf8d6e0586b0a20c7

access(all) fun main(electionId: UInt64): &{ElectionStandard.ElectionPublic}? {
    // Grab an unauthorized reference to the deployer account from the VoteBooth or ElectionStandard contract
    let deployerAccount: &Account = getAccount(VoteBooth.deployerAddress)

    // Use this account reference to get a public reference to the ElectionIndex
    let electionIndexRef: &{VoteBooth.ElectionIndexPublic} = deployerAccount.capabilities.borrow<&{VoteBooth.ElectionIndexPublic}>(VoteBooth.electionIndexPublicPath) ??
    panic(
        "Unable to retrieve a valid &{VoteBooth.ElectionIndexPublic} at"
        .concat(VoteBooth.electionIndexPublicPath.toString())
        .concat(" from account ")
        .concat(VoteBooth.deployerAddress.toString())
    )

    // Use the ElectionIndexRef to get the reference in question
    return electionIndexRef.getPublicElectionReference(_electionId: electionId)
}