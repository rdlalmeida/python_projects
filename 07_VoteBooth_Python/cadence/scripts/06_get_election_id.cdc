/**
 ""
    NOTE: When the &VoteBoxStandard.VoteBoxPublic version only works if the VoteBox has a Ballot in store for the electionId provided. If not, the function returns nil

    @param electionId (UInt64) The election identifier for the Election resource whose parameter is to be returned to.
    @param voteboxAddress (Address?) The account address to use to retrieve the public version of the VoteBox resource. This input can be set to a nil to retrieve the parameter in question directly from the Election resource reference.

    @returns (UInt64) Returns the electionId of the Election, straight from the loaded resource, if it exists. Otherwise, the process panics at the offending step.
**/
import VoteBooth from 0x287f5c8b0865c516
import ElectionStandard from 0x287f5c8b0865c516
import VoteBoxStandard from 0x287f5c8b0865c516

access(all) fun main(electionId: UInt64, voteboxAddress: Address?): UInt64? {
    if (voteboxAddress == nil) {
        let deployerAccount: &Account = getAccount(VoteBooth.deployerAddress)

        let electionIndexRef: &{VoteBooth.ElectionIndexPublic} = deployerAccount.capabilities.borrow<&{VoteBooth.ElectionIndexPublic}>(VoteBooth.electionIndexPublicPath) ??
        panic(
            "Unable to get a valid &{VoteBooth.ElectionIndexPublic} at `VoteBooth.electionIndexPublicPath.toString()` from account `deployerAccount.address.toString()`"
        )

        let electionRef: &{ElectionStandard.ElectionPublic} = electionIndexRef.getPublicElectionReference(_electionId: electionId)!

        return electionRef.getElectionId()
    }
    else {
        let voteboxAccount: &Account = getAccount(voteboxAddress!)
        let voteboxRef: &{VoteBoxStandard.VoteBoxPublic} = voteboxAccount.capabilities.borrow<&{VoteBoxStandard.VoteBoxPublic}>(VoteBoxStandard.voteBoxPublicPath) ??
        panic(
            "Unable to get a valid &{VoteBoxStandard.VoteBoxPublic} at `VoteBoxStandard.voteBoxPublicPath.toString()` from account `voteboxAddress!.toString()`"
        )

        return voteboxRef.getElectionId(electionId: electionId)
    }
}