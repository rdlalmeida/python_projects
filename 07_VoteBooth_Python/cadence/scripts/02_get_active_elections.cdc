/**
    Simple script to return an array with all the electionIds from active Elections in the given account provided as input argument. This script has an optional Address input. If this input is provided (non-nil), this script grabs a public reference to a VoteBox resource and returns the list of active electionIds for stored Ballots. In the absence of this input, i.e., this argument passed as nil, then this script loads the public reference to an ElectionIndex resource from the deployer address for any of the project contracts, and returns the associated list of active electionIds.

 ""
**/
import VoteBooth from 0x287f5c8b0865c516
import ElectionStandard from 0x287f5c8b0865c516
import VoteBoxStandard from 0x287f5c8b0865c516

access(all) fun main(voteboxAddress: Address?): [UInt64] {
    if (voteboxAddress == nil) {
        let deployerAccount: &Account = getAccount(VoteBooth.deployerAddress)

        let electionIndexRef: &{VoteBooth.ElectionIndexPublic} = deployerAccount.capabilities.borrow<&{VoteBooth.ElectionIndexPublic}>(VoteBooth.electionIndexPublicPath) ??
        panic(
            "Unable to retrieve a valid &{VoteBooth.ElectionIndexPublic} at `VoteBooth.electionIndexPublicPath.toString()` from account `deployerAccount.address.toString()`"
        )

        return electionIndexRef.getActiveElectionIds()
    }
    else {
        let voteboxAccount: &Account = getAccount(voteboxAddress!)
        let voteboxRef: &{VoteBoxStandard.VoteBoxPublic} = voteboxAccount.capabilities.borrow<&{VoteBoxStandard.VoteBoxPublic}>(VoteBoxStandard.voteBoxPublicPath) ??
        panic(
            "Unable to bet a valid &{VoteBoxStandard.VoteBoxPublic} at `VoteBoxStandard.voteBoxPublicPath.toString()` for account `voteboxAddress!.toString()`"
        )

        return voteboxRef.getActiveElectionIds()
    }
}