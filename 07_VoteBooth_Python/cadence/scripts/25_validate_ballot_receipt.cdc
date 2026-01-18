/**
    This script validates if a ballotReceipt provided as argument is a valid one, i.e., there is a record for it in the VoteBox instance in the voter address account provided, under the electionId provided as well. Any problems encountered during this validation step triggers the return of a false.

    @param voterAddress (Address): The account address to use to retrieve a potential VoteBox resource from.
    @param electionId (UInt64): The election identifier to use to validate the ballotReceipt upon.
    @param ballotReceipt (UInt64): The ballotReceipt value to validate against the VoteBox and electionId provided.
**/
import VoteBoxStandard from 0xf8d6e0586b0a20c7

access(all) fun main(voterAddress: Address, electionId: UInt64, ballotReceipt: UInt64): Bool {
    // Grab a public reference to the account for the address provided
    let voterAccount: &Account = getAccount(voterAddress)

    // Use the account reference to get a reference to a VoteBox, if one exists
    let voteboxRef: &{VoteBoxStandard.VoteBoxPublic}? = voterAccount.capabilities.borrow<&{VoteBoxStandard.VoteBoxPublic}>(VoteBoxStandard.voteBoxPublicPath)

    if (voteboxRef == nil) {
        // No valid VoteBox found. Return false
        return false
    }
    else {
        // Forward the script data to the proper VoteBox function
        return voteboxRef!.validateBallotReceipt(electionId: electionId, ballotReceipt: ballotReceipt)
    }
}