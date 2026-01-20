/**
    This apparently simple script is actually needed due to the convoluted way in which I'm saving Ballots in this system. This script returns the ballotId for a Ballot stored under the VoteBox stored under the address provided as input, under the electionId key also provided as input.

    @param voteboxAddress (Address) The address of the account where the VoteBox reference should be retrieved from.
    @param electionId (UInt64) The election identifier where the Ballot should be stored under.

    @returns UInt64? If a Ballot exists for the VoteBox and electionId provided, this script returns its ballotId. Otherwise it returns nil.
**/
import VoteBoxStandard from 0x287f5c8b0865c516

access(all) fun main(electionId: UInt64, voteboxAddress: Address): UInt64? {
    let voteboxRef: &{VoteBoxStandard.VoteBoxPublic} = getAccount(voteboxAddress).capabilities.borrow<&{VoteBoxStandard.VoteBoxPublic}>(VoteBoxStandard.voteBoxPublicPath) ??
    panic(
        "Unable to get a valid &{VoteBoxStandard.VoteBoxPublic} at `VoteBoxStandard.voteBoxPublicPath.toString()` from account `voteboxAddress.toString()`"
    )

    return voteboxRef.getBallotId(electionId: electionId)
}