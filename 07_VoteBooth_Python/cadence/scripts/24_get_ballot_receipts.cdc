/**
    This script fetches and returns the set of ballotReceipts submitted to the VoteBox in the account address provided as argument, under the electionId provided as well, if one exists.

    @param voterAddress (Address): The account address to retrieved the ballotReceipt list from.
    @param electionId (UInt64): The Election identifier to use to retrieve the ballotReceipt list.

    @return [UInt64]?: If the account address provided as a VoteBox resource and the VoteBox has an entry under the electionId provided as argument, this script returns the list of ballotReceipts set to it. Otherwise returns a nil.
**/
import VoteBoxStandard from 0xf8d6e0586b0a20c7

access(all) fun main(voterAddress: Address, electionId: UInt64): [UInt64]? {
    // Grab a public reference to the account from the address provided
    let voterAccount: &Account = getAccount(voterAddress)

    // Use the account reference to get a reference to a VoteBox, if one exists
    let voteboxRef: &{VoteBoxStandard.VoteBoxPublic}? = voterAccount.capabilities.borrow<&{VoteBoxStandard.VoteBoxPublic}>(VoteBoxStandard.voteBoxPublicPath)

    // Check if the reference above is nil
    if (voteboxRef == nil) {
        // No valid VoteBox resource found for the account in question. Return nil
        return nil
    }
    else {
        // Got a valid VoteBox. Return the ballotReceipts array from it
        return voteboxRef!.getBallotReceipts(electionId: electionId)
    }
}