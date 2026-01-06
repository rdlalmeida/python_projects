/**
    Since I can invoke this function either directly from an &ElectionStandard.ElectionPublic reference or from a &VoteBoxStandard.VoteBoxPublic one as well, I want this one script to be able to do both. Retrieving this data from the ElectionStandard.ElectionPublic only requires a valid electionId, but the one from the &VoteBoxStandard.VoteBoxPublic needs the address to the user account provided as well. As such, each of the following scripts accept two inputs, the second one is set as an optional (the voter address). If both inputs are provided, this script runs the &VoteBoxStandard.VoteBoxPublic version. If the voter address is a nil instead, then the &ElectionStandard.ElectionPublic one is invoked instead.
    NOTE: When the &VoteBoxStandard.VoteBoxPublic version only works if the VoteBox has a Ballot in store for the electionId provided. If not, the function returns nil

    @param electionId (UInt64) The election identifier for the Election resource whose parameter is to be returned to.
    @param voteboxAddress (Address?) The account address to use to retrieve the public version of the VoteBox resource. This input can be set to a nil to retrieve the parameter in question directly from the Election resource reference.

    @returns (String?) Returns the ballot of the Election, if it exists.
**/
import ElectionStandard from 0xf8d6e0586b0a20c7
import VoteBoxStandard from 0xf8d6e0586b0a20c7
import VoteBooth from 0xf8d6e0586b0a20c7

access(all) fun main(electionId: UInt64, voteboxAddress: Address?): String? {
    if (voteboxAddress == nil) {
        let deployerAccount: &Account = getAccount(VoteBooth.deployerAddress)

        let electionIndexRef: &{VoteBooth.ElectionIndexPublic} = deployerAccount.capabilities.borrow<&{VoteBooth.ElectionIndexPublic}>(VoteBooth.electionIndexPublicPath) ??
        panic(
            "Unable to get a valid &{VoteBooth.ElectionIndexPublic} at `VoteBooth.electionIndexPublicPath.toString()` from account `deployerAccount.address.toString()`"
        )

        let electionRef: &{ElectionStandard.ElectionPublic} = electionIndexRef.getPublicElectionReference(_electionId: electionId)!

        return electionRef.getElectionBallot()
    }
    else {
        let voteboxAccount: &Account = getAccount(voteboxAddress!)
        let voteboxRef: &{VoteBoxStandard.VoteBoxPublic} = voteboxAccount.capabilities.borrow<&{VoteBoxStandard.VoteBoxPublic}>(VoteBoxStandard.voteBoxPublicPath) ??
        panic(
            "Unable to get a valid &{VoteBoxStandard.VoteBoxPublic} at `VoteBoxStandard.voteBoxPublicPath.toString()` from account `voteboxAddress!.toString()`"
        )

        return voteboxRef.getElectionBallot(electionId: electionId)
    }
}